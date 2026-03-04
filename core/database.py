# core/database.py
import os
import json
import shutil
from datetime import datetime
import logging

SALT_FILE = "vault.salt"
DATA_FILE = "vault.dat"
CONFIG_FILE = "vault.cfg"
BACKUP_FOLDER = "backups"
MAX_BACKUPS = 10

logger = logging.getLogger('GameVault.Core.database')
class Database:
    """Управление данными и бэкапами"""
    
    def __init__(self, crypto):
        self.crypto = crypto
        self.data = {}
        self.config = {}
        
    def load_config(self):
        """Загрузка конфигурации"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}
        return self.config
    
    def save_config(self):
        """Сохранение конфигурации"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_data(self, password: str):
        """Загрузка данных с паролем"""
        if not os.path.exists(SALT_FILE) or not os.path.exists(DATA_FILE):
            return False, "Нет сохраненных данных"
        
        try:
            with open(SALT_FILE, 'rb') as f:
                salt = f.read()
            
            self.crypto.set_password(password, salt)
            
            with open(DATA_FILE, 'rb') as f:
                encrypted = f.read()
            
            self.data = self.crypto.decrypt(encrypted)
            return True, "Данные загружены"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def create_new_vault(self, password: str, email: str = None):
        """Создание нового хранилища"""
        try:
            self.crypto.set_password(password)
            
            # Сохраняем соль
            with open(SALT_FILE, 'wb') as f:
                f.write(self.crypto.salt)
            
            self.data = {}
            if email:
                self.config['email'] = email
            
            self.save_data()
            self.save_config()
            return True, "Хранилище создано"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def save_data(self):
        """Сохранение данных"""
        if self.crypto.cipher:
            encrypted = self.crypto.encrypt(self.data)
            with open(DATA_FILE, 'wb') as f:
                f.write(encrypted)
            
            backup_file = self.create_backup()
            
            # Автоматическая загрузка в облако если настроено
            if backup_file and 'cloud' in self.config:
                cloud_config = self.config['cloud']
                if cloud_config.get('auto_upload') and 'password' in cloud_config:
                    try:
                        from .cloud_storage import CloudStorage
                        cloud = CloudStorage(self.crypto)
                        password = self.crypto.decrypt_password(cloud_config['password'])
                        if password:
                            cloud.upload_backup(
                                cloud_config['email'],
                                password,
                                backup_file,
                                cloud_config.get('folder', 'GameVault_Backups')
                            )
                    except:
                        pass  # Не прерываем сохранение если облако не работает
            
            return True
        return False
    
    def create_backup(self) -> str:
        """Создание резервной копии"""
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_FOLDER, f"backup_{timestamp}.dat")
        
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, backup_file)
            
            # Удаляем старые бэкапы
            backups = sorted([f for f in os.listdir(BACKUP_FOLDER) 
                            if f.startswith("backup_")])
            while len(backups) > MAX_BACKUPS:
                os.remove(os.path.join(BACKUP_FOLDER, backups[0]))
                backups.pop(0)
            
            return backup_file
        return None
    
    def get_backups(self):
        """Получение списка бэкапов"""
        if not os.path.exists(BACKUP_FOLDER):
            return []
        
        backups = []
        for f in sorted(os.listdir(BACKUP_FOLDER)):
            if f.startswith("backup_"):
                path = os.path.join(BACKUP_FOLDER, f)
                timestamp = f.replace("backup_", "").replace(".dat", "")
                try:
                    size = os.path.getsize(path)
                    date = f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
                    backups.append({
                        'name': f,
                        'path': path,
                        'size': size,
                        'date': date
                    })
                except:
                    continue
        return backups
    
    def restore_backup(self, backup_path: str) -> bool:
        """Восстановление из бэкапа"""
        try:
            shutil.copy2(backup_path, DATA_FILE)
            return True
        except:
            return False
    
    def add_account(self, account: dict):
        """Добавление аккаунта"""
        account['created'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account_id = str(len(self.data) + 1)
        self.data[account_id] = account
        self.save_data()
        return account_id
    
    def delete_account(self, account_id: str):
        """Удаление аккаунта"""
        if account_id in self.data:
            del self.data[account_id]
            # Перенумеровываем
            new_data = {}
            for i, (_, value) in enumerate(self.data.items(), 1):
                new_data[str(i)] = value
            self.data = new_data
            self.save_data()
            return True
        return False
    
    def update_account(self, account_id: str, account: dict):
        """Обновление аккаунта"""
        if account_id in self.data:
            self.data[account_id].update(account)
            self.save_data()
            return True
        return False
    
    def search_accounts(self, query: str):
        """Поиск аккаунтов"""
        query = query.lower()
        results = []
        for acc_id, acc in self.data.items():
            if query in acc.get('game', '').lower() or \
               query in acc.get('login', '').lower():
                results.append((acc_id, acc))
        return results