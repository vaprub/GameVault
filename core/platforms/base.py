# core/platforms/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class PlatformBase(ABC):
    """Абстрактный базовый класс для всех платформ."""
    
    def __init__(self, database, crypto):
        self.db = database
        self.crypto = crypto
        self.name = "Base"
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any], account_id: Optional[int] = None) -> bool:
        """Аутентификация на платформе (сохраняет токены)."""
        pass
    
    @abstractmethod
    def fetch_games(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает список игр с платформы.
        Возвращает список словарей с ключами: name, platform, playtime, last_played.
        """
        pass
    
    def sync_games(self, account_id: int) -> int:
        """Синхронизирует игры для указанного аккаунта (заменяет старые)."""
        games = self.fetch_games(account_id)
        # Удаляем старые игры
        self.db.delete_all_games(account_id)
        # Добавляем новые
        for game in games:
            self.db.add_game(account_id, game)
        return len(games)
    
    def get_token(self, account_id: Optional[int] = None) -> Optional[str]:
        """Получает зашифрованный токен из БД и расшифровывает."""
        enc_token = self.db.get_token(self.name.lower(), account_id)
        if enc_token:
            return self.crypto.decrypt_password(enc_token)
        return None
    
    def save_token(self, token: str, account_id: Optional[int] = None):
        """Шифрует и сохраняет токен."""
        enc_token = self.crypto.encrypt_password(token)
        self.db.save_token(self.name.lower(), enc_token, account_id)