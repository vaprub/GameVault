# core/crypto.py
import hashlib
import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

CONFIG_FILE = "vault_config.json"


class CryptoManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.salt = None
        self.key = None
        self.fernet = None
        self._load_config()

    def _load_config(self):
        """Загружает соль из конфигурационного файла, если он существует."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.salt = base64.b64decode(config['salt'])
        else:
            self.salt = None

    def _save_config(self):
        """Сохраняет соль в конфигурационный файл."""
        if self.salt is None:
            raise ValueError("Cannot save config without salt")
        config = {
            'salt': base64.b64encode(self.salt).decode('ascii')
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def derive_key(self, password: str, salt: bytes = None) -> (bytes, bytes):
        """Производит ключ из пароля и соли. Если соль не передана, генерирует новую."""
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def create_new_vault(self, password: str):
        """Создаёт новое хранилище: генерирует соль и ключ, сохраняет конфиг."""
        self.key, self.salt = self.derive_key(password)
        self._save_config()
        self.fernet = Fernet(self.key)

    def unlock_vault(self, password: str):
        """Разблокирует существующее хранилище: использует сохранённую соль для получения ключа."""
        if self.salt is None:
            raise Exception("No salt found. Maybe vault is not initialized.")
        self.key, _ = self.derive_key(password, self.salt)
        self.fernet = Fernet(self.key)

    def is_initialized(self) -> bool:
        """Проверяет, существует ли конфигурационный файл (т.е. было ли создано хранилище)."""
        return os.path.exists(self.config_file)

    def encrypt(self, data: str) -> str:
        if not self.fernet:
            raise Exception("Crypto not initialized. Call create_new_vault or unlock_vault first.")
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        if not self.fernet:
            raise Exception("Crypto not initialized.")
        return self.fernet.decrypt(token.encode()).decode()
