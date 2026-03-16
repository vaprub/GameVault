# core/database.py
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger('GameVault.Database')

class Database:
    """Работа с SQLite базой данных."""

    def __init__(self, crypto, db_path="gamevault.db"):
        self.crypto = crypto
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """Возвращает соединение с БД (с поддержкой внешних ключей)."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Создаёт таблицы, если их нет."""
        with self._get_conn() as conn:
            # Таблица аккаунтов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    login TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT,
                    email_password TEXT,
                    notes TEXT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Таблица игр (связь с аккаунтом)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    game_name TEXT NOT NULL,
                    game_platform TEXT,
                    playtime INTEGER DEFAULT 0,
                    last_played TIMESTAMP,
                    appid INTEGER,
                    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                )
            ''')
            # Таблица токенов платформ
            conn.execute('''
                CREATE TABLE IF NOT EXISTS platform_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL UNIQUE,
                    token_data TEXT NOT NULL,
                    account_id INTEGER,
                    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                )
            ''')
            # Таблица для кеширования названий игр по appid
            conn.execute('''
                CREATE TABLE IF NOT EXISTS game_names (
                    appid INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    # ---------- Работа с аккаунтами ----------
    def add_account(self, account: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cur = conn.execute('''
                INSERT INTO accounts (platform, login, password, email, email_password, notes)
                VALUES (:platform, :login, :password, :email, :email_password, :notes)
            ''', account)
            return cur.lastrowid

    def get_accounts(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute('SELECT * FROM accounts ORDER BY platform, login')
            return [dict(row) for row in cur.fetchall()]

    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_account(self, account_id: int, updates: Dict[str, Any]) -> bool:
        with self._get_conn() as conn:
            set_clause = ', '.join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [account_id]
            cur = conn.execute(f'UPDATE accounts SET {set_clause} WHERE id = ?', values)
            return cur.rowcount > 0

    def delete_account(self, account_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            return cur.rowcount > 0

    # ---------- Работа с играми ----------
    def add_game(self, account_id: int, game: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cur = conn.execute('''
                INSERT INTO games (account_id, game_name, game_platform, playtime, last_played, appid)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (account_id, game['name'], game.get('platform', ''), game.get('playtime', 0),
                  game.get('last_played'), game.get('appid')))
            return cur.lastrowid

    def get_games(self, account_id: int) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute('SELECT * FROM games WHERE account_id = ? ORDER BY game_name', (account_id,))
            return [dict(row) for row in cur.fetchall()]

    def delete_all_games(self, account_id: int) -> int:
        with self._get_conn() as conn:
            cur = conn.execute('DELETE FROM games WHERE account_id = ?', (account_id,))
            return cur.rowcount

    def update_game(self, game_id: int, updates: Dict[str, Any]) -> bool:
        """Обновляет игру по её ID."""
        with self._get_conn() as conn:
            set_clause = ', '.join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [game_id]
            cur = conn.execute(f'UPDATE games SET {set_clause} WHERE id = ?', values)
            return cur.rowcount > 0

    def delete_game(self, game_id: int) -> bool:
        """Удаляет игру по её ID."""
        with self._get_conn() as conn:
            cur = conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
            return cur.rowcount > 0

    def search_games(self, query: str) -> List[Dict[str, Any]]:
        """
        Ищет игры по названию и возвращает список аккаунтов, у которых есть такие игры.
        Каждый элемент списка содержит информацию об аккаунте и список игр.
        """
        with self._get_conn() as conn:
            # Сначала находим игры, подходящие под запрос
            like_query = f'%{query}%'
            cur = conn.execute('''
                SELECT games.*, accounts.*
                FROM games
                JOIN accounts ON games.account_id = accounts.id
                WHERE games.game_name LIKE ?
                ORDER BY accounts.login, games.game_name
            ''', (like_query,))
            rows = cur.fetchall()
            # Группируем по аккаунтам
            accounts_dict = {}
            for row in rows:
                row_dict = dict(row)
                account_id = row_dict['account_id']
                if account_id not in accounts_dict:
                    # Копируем данные аккаунта
                    account_data = {
                        'id': row_dict['id'],
                        'platform': row_dict['platform'],
                        'login': row_dict['login'],
                        'password': row_dict['password'],
                        'email': row_dict['email'],
                        'email_password': row_dict['email_password'],
                        'notes': row_dict['notes'],
                        'created': row_dict['created'],
                        'games': []
                    }
                    accounts_dict[account_id] = account_data
                accounts_dict[account_id]['games'].append({
                    'id': row_dict['id'],
                    'game_name': row_dict['game_name'],
                    'game_platform': row_dict['game_platform'],
                    'playtime': row_dict['playtime'],
                    'last_played': row_dict['last_played'],
                    'appid': row_dict['appid']
                })
            return list(accounts_dict.values())

    # ---------- Работа с токенами платформ ----------
    def save_token(self, platform: str, token_data: str, account_id: Optional[int] = None):
        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO platform_tokens (platform, token_data, account_id)
                VALUES (?, ?, ?)
            ''', (platform, token_data, account_id))

    def get_token(self, platform: str, account_id: Optional[int] = None) -> Optional[str]:
        with self._get_conn() as conn:
            if account_id is None:
                cur = conn.execute('SELECT token_data FROM platform_tokens WHERE platform = ? AND account_id IS NULL', (platform,))
            else:
                cur = conn.execute('SELECT token_data FROM platform_tokens WHERE platform = ? AND account_id = ?', (platform, account_id))
            row = cur.fetchone()
            return row['token_data'] if row else None

    # ---------- Кеширование названий игр ----------
    def get_cached_game_name(self, appid: int) -> Optional[str]:
        with self._get_conn() as conn:
            cur = conn.execute('SELECT name FROM game_names WHERE appid = ?', (appid,))
            row = cur.fetchone()
            return row['name'] if row else None

    def save_game_name(self, appid: int, name: str):
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO game_names (appid, name) VALUES (?, ?)', (appid, name))

    # ---------- Поиск аккаунтов (старый, расширим его) ----------
    def search_accounts(self, query: str) -> List[Dict[str, Any]]:
        """Ищет аккаунты по логину, платформе, заметкам, а также по играм."""
        # Сначала ищем по аккаунтам напрямую
        with self._get_conn() as conn:
            like_query = f'%{query}%'
            cur = conn.execute('''
                SELECT * FROM accounts
                WHERE login LIKE ? OR platform LIKE ? OR notes LIKE ?
                ORDER BY platform, login
            ''', (like_query, like_query, like_query))
            accounts = [dict(row) for row in cur.fetchall()]

        # Затем добавляем аккаунты, найденные через игры (без дубликатов)
        game_accounts = self.search_games(query)
        existing_ids = {a['id'] for a in accounts}
        for acc in game_accounts:
            if acc['id'] not in existing_ids:
                # Убираем поле games, так как мы возвращаем только аккаунты
                acc_copy = {k: v for k, v in acc.items() if k != 'games'}
                accounts.append(acc_copy)
                existing_ids.add(acc['id'])

        return accounts