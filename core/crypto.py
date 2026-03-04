# core/crypto.py
import os
import base64
import json
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger('GameVault.Core.crypto')
class CryptoManager:
    """Управление шифрованием и мастер-паролем"""
    
    def __init__(self):
        self.key = None
        self.cipher = None
        self.salt = None
        
    def generate_key_from_password(self, password: str, salt: bytes = None):
        """Генерация ключа из пароля"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def set_password(self, password: str, salt: bytes = None):
        """Установка мастер-пароля"""
        self.key, self.salt = self.generate_key_from_password(password, salt)
        self.cipher = Fernet(self.key)
        return True
    
    def encrypt(self, data: any) -> bytes:
        """Шифрование данных"""
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> any:
        """Дешифровка данных"""
        decrypted = self.cipher.decrypt(encrypted_data)
        try:
            return json.loads(decrypted.decode('utf-8'))
        except:
            return decrypted.decode('utf-8')
    
    def encrypt_password(self, password: str) -> str:
        """Шифрование пароля для хранения"""
        if self.cipher:
            return self.cipher.encrypt(password.encode()).decode()
        return None
    
    def decrypt_password(self, encrypted: str) -> str:
        """Дешифровка пароля"""
        if self.cipher and encrypted:
            try:
                return self.cipher.decrypt(encrypted.encode()).decode()
            except:
                return None
        return None
    
    def generate_password(self, length: int = 16) -> str:
        """Генерация надежного пароля"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))