# core/database.py
import json
import os
import logging
from typing import List, Dict

logger = logging.getLogger('GameVault.Database')


class Database:
    def __init__(self, crypto, data_file="vault.json.enc"):
        self.crypto = crypto
        self.data_file = data_file
        self.accounts = []
        # Не загружаем сразу, т.к. crypto может быть не инициализирован
        # Загрузка будет вызвана явно после успешного входа

    def load(self):
        """Загружает и расшифровывает данные из файла."""
        if not os.path.exists(self.data_file):
            self.accounts = []
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                encrypted = f.read()
            decrypted = self.crypto.decrypt(encrypted)
            self.accounts = json.loads(decrypted)
            logger.info(f"Loaded {len(self.accounts)} accounts from {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            raise  # Пробрасываем выше, чтобы показать пользователю

    def save(self):
        """Шифрует и сохраняет данные в файл."""
        try:
            plain = json.dumps(self.accounts, ensure_ascii=False, indent=2)
            encrypted = self.crypto.encrypt(plain)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            logger.info(f"Saved {len(self.accounts)} accounts to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            raise

    def add_account(self, name, email, password, note=""):
        """Добавляет новую учётную запись и сохраняет хранилище."""
        self.accounts.append({
            "name": name,
            "email": email,
            "password": password,
            "note": note
        })
        self.save()

    def get_accounts(self) -> List[Dict]:
        """Возвращает список учётных записей (без копирования, для производительности)."""
        return self.accounts

    def clear_memory(self):
        """Затирает все учётные записи в памяти (для автоблокировки)."""
        # Перезаписываем каждый элемент
        for i in range(len(self.accounts)):
            self.accounts[i] = None
        self.accounts = []
        logger.info("Database memory cleared.")
