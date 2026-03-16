# core/platforms/steam.py
import logging
import json
import threading
import time
import requests
from typing import List, Dict, Any, Optional
from .base import PlatformBase
from steam.client import SteamClient
from steam.webauth import WebAuth, EmailCodeRequired, TwoFactorCodeRequired

logger = logging.getLogger('GameVault.Platform.Steam')

class AuthCodeRequired(Exception):
    """Исключение, выбрасываемое когда для входа требуется код (email или 2FA)."""
    def __init__(self, is_2fa, message=""):
        self.is_2fa = is_2fa
        self.message = message
        super().__init__(message)

class SteamPlatform(PlatformBase):
    """Реализация для Steam с двухэтапной аутентификацией: webauth для кода, затем client для входа."""

    def __init__(self, database, crypto):
        super().__init__(database, crypto)
        self.name = "Steam"
        self.client: Optional[SteamClient] = None
        self.steam_id = None

    def get_code_via_webauth(self, account_id: int) -> tuple:
        """
        Получает код через webauth, выбрасывает исключение AuthCodeRequired с информацией о типе кода.
        Возвращает (code, is_2fa) если код введён, иначе None.
        """
        account = self.db.get_account(account_id)
        login = account.get('login')
        password = account.get('password')

        user = WebAuth(login)
        try:
            user.login(password)
            # Если дошли сюда, значит код не потребовался (маловероятно)
            return None
        except EmailCodeRequired:
            raise AuthCodeRequired(False, "Email code required")
        except TwoFactorCodeRequired:
            raise AuthCodeRequired(True, "2FA code required")
        except Exception as e:
            logger.exception("WebAuth error")
            raise

    def authenticate(self, account_id: int, code: Optional[str] = None, is_2fa: bool = False) -> bool:
        """
        Аутентификация через SteamClient.
        Если код не передан, сначала пытается получить его через webauth (выбрасывает AuthCodeRequired).
        Если код передан, использует его для входа через client.
        """
        account = self.db.get_account(account_id)
        if not account:
            logger.error(f"Account {account_id} not found")
            return False

        login = account.get('login')
        password = account.get('password')
        if not login or not password:
            logger.error(f"Account {account_id} missing login/password")
            return False

        # Если код не передан, запускаем процесс webauth для получения кода
        if code is None:
            # Это выбросит AuthCodeRequired, которое будет поймано в GUI
            self.get_code_via_webauth(account_id)
            return False  # сюда не дойдём, если выброшено исключение

        # Если код передан, входим через client
        self.client = SteamClient()
        login_complete = threading.Event()
        login_success = False
        login_error = None

        @self.client.on(self.client.EVENT_LOGGED_ON)
        def on_logged_on():
            nonlocal login_success
            self.steam_id = str(self.client.steam_id)
            login_success = True
            login_complete.set()
            logger.info(f"Logged on, Steam ID: {self.steam_id}")

        @self.client.on(self.client.EVENT_ERROR)
        def on_error(eresult):
            nonlocal login_error
            logger.error(f"Login error: {eresult}")
            login_error = eresult
            login_complete.set()

        try:
            if is_2fa:
                self.client.login(login, password, two_factor_code=code)
            else:
                self.client.login(login, password, auth_code=code)
        except Exception as e:
            logger.exception("Error calling client.login")
            return False

        # Ждём завершения процесса входа (макс 60 сек)
        if not login_complete.wait(timeout=60):
            logger.error("Login timeout")
            return False

        if login_error is not None:
            logger.error(f"Login failed: {login_error}")
            return False

        return login_success

    def _get_game_name(self, appid: int) -> str:
        """Возвращает название игры по appid, используя кеш БД и Steam Store API."""
        cached = self.db.get_cached_game_name(appid)
        if cached:
            return cached

        try:
            resp = requests.get(
                f'https://store.steampowered.com/api/appdetails?appids={appid}',
                timeout=5,
                headers={'User-Agent': 'GameVault/1.0'}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get(str(appid), {}).get('success'):
                    name = data[str(appid)]['data']['name']
                    self.db.save_game_name(appid, name)
                    return name
        except Exception as e:
            logger.warning(f"Failed to fetch name for appid {appid}: {e}")

        return f"AppID:{appid}"

    def fetch_games(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает список игр через клиентский метод Player.ClientGetLastPlayedTimes#1.
        Обогащает названия через Store API с кешированием.
        """
        if not self.client or not self.client.logged_on:
            raise Exception("Steam client not authenticated")

        method_name = 'Player.ClientGetLastPlayedTimes#1'
        params = {'min_last_played': 0}

        try:
            response = self.client.send_um_and_wait(method_name, params, timeout=15)
            if response is None:
                raise Exception("No response from server (timeout)")

            games_proto = response.body.games
            games = []
            for game_proto in games_proto:
                appid = getattr(game_proto, 'appid', 0)
                playtime = getattr(game_proto, 'playtime_forever', 0) // 60
                last_played = getattr(game_proto, 'last_playtime', None)
                name = self._get_game_name(appid)
                games.append({
                    'name': name,
                    'platform': 'Steam',
                    'playtime': playtime,
                    'last_played': last_played,
                    'appid': appid,
                })
            logger.info(f"Fetched {len(games)} games from Steam for account_id={account_id}")
            return games
        except Exception as e:
            logger.error(f"Steam fetch games error: {e}")
            raise