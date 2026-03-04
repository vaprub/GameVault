# core/cloud_storage.py
import os
import imaplib
import smtplib
import email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json
import time
import logging
from logging.handlers import RotatingFileHandler

# Настройка логирования
def setup_logger():
    """Настройка логгера для облачного хранилища"""
    logger = logging.getLogger('GameVault.Cloud')
    logger.setLevel(logging.DEBUG)
    
    # Создаем папку для логов если нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Файловый handler с ротацией (10 MB, 5 файлов)
    file_handler = RotatingFileHandler(
        'logs/cloud.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

class CloudStorage:
    """Работа с облачными хранилищами через почту"""
    
    # Настройки IMAP для разных почтовых сервисов
    IMAP_SERVERS = {
        'gmail.com': 'imap.gmail.com',
        'yandex.ru': 'imap.yandex.ru',
        'ya.ru': 'imap.yandex.ru',
        'mail.ru': 'imap.mail.ru',
        'bk.ru': 'imap.mail.ru',
        'list.ru': 'imap.mail.ru',
        'inbox.ru': 'imap.mail.ru',
        'rambler.ru': 'imap.rambler.ru',
        'outlook.com': 'imap-mail.outlook.com',
        'hotmail.com': 'imap-mail.outlook.com',
        'live.com': 'imap-mail.outlook.com',
        'icloud.com': 'imap.mail.me.com',
        'yahoo.com': 'imap.mail.yahoo.com'
    }
    
    def __init__(self, crypto):
        self.crypto = crypto
        self.imap_server = None
        self.mail = None
        self.logger = setup_logger()
        self.logger.info("CloudStorage инициализирован")
        
    def get_imap_server(self, email):
        """Получение IMAP сервера по email"""
        domain = email.split('@')[-1].lower()
        self.logger.debug(f"Определение IMAP сервера для домена: {domain}")
        
        if domain in self.IMAP_SERVERS:
            server = self.IMAP_SERVERS[domain]
            self.logger.debug(f"Найден сервер: {server}")
            return server
        
        for key, value in self.IMAP_SERVERS.items():
            if key in domain:
                self.logger.debug(f"Найден по частичному совпадению: {value}")
                return value
        
        self.logger.warning(f"Неизвестный домен {domain}, используется Gmail")
        return 'imap.gmail.com'
    
    def connect_imap(self, email, password):
        """Подключение к IMAP серверу"""
        self.logger.info(f"Подключение к IMAP для {email}")
        try:
            server = self.get_imap_server(email)
            self.logger.debug(f"Сервер: {server}")
            
            self.mail = imaplib.IMAP4_SSL(server)
            self.mail.login(email, password)
            self.logger.info("Успешное подключение к IMAP")
            return True, "Подключено"
            
        except imaplib.IMAP4.error as e:
            self.logger.error(f"Ошибка IMAP аутентификации: {str(e)}")
            return False, f"Ошибка аутентификации: {str(e)}"
        except Exception as e:
            self.logger.error(f"Ошибка подключения к IMAP: {str(e)}")
            return False, str(e)
    
    def disconnect(self):
        """Отключение от IMAP"""
        if self.mail:
            try:
                self.mail.logout()
                self.logger.debug("Отключение от IMAP")
            except Exception as e:
                self.logger.error(f"Ошибка при отключении: {str(e)}")
            finally:
                self.mail = None
    
    def upload_backup(self, email, password, backup_file, folder='GameVault_Backups'):
        """Загрузка бэкапа в облако (как черновик)"""
        self.logger.info(f"Загрузка бэкапа {backup_file} в папку {folder}")
        
        if not os.path.exists(backup_file):
            self.logger.error(f"Файл бэкапа не найден: {backup_file}")
            return False, f"Файл не найден: {backup_file}"
        
        try:
            # Подключаемся
            success, msg = self.connect_imap(email, password)
            if not success:
                self.logger.error(f"Ошибка подключения: {msg}")
                return False, f"Ошибка подключения: {msg}"
            
            # Создаем папку если нет
            try:
                self.mail.create(folder)
                self.logger.debug(f"Создана папка {folder}")
            except:
                self.logger.debug(f"Папка {folder} уже существует")
            
            # Создаем письмо с бэкапом
            msg = MIMEMultipart()
            msg['Subject'] = f"GameVault Backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg['From'] = email
            msg['To'] = email
            
            # Добавляем описание
            body = f"""
            Автоматический бэкап GameVault
            Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Размер: {os.path.getsize(backup_file)} байт
            
            Это автоматическое сообщение. Не удаляйте его!
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Добавляем файл бэкапа
            with open(backup_file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{os.path.basename(backup_file)}"'
                )
                msg.attach(part)
            
            # Сохраняем как черновик в указанной папке
            self.mail.select(folder)
            self.mail.append(
                folder,
                '\\Drafts',
                imaplib.Time2Internaldate(time.time()),
                msg.as_string().encode('utf-8')
            )
            
            self.disconnect()
            self.logger.info("Бэкап успешно загружен в облако")
            return True, "Бэкап загружен в облако"
            
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке бэкапа: {str(e)}")
            self.disconnect()
            return False, str(e)
    
    def list_backups(self, email, password, folder='GameVault_Backups'):
        """Получение списка бэкапов из облака"""
        self.logger.info(f"Получение списка бэкапов из папки {folder}")
        
        try:
            success, msg = self.connect_imap(email, password)
            if not success:
                self.logger.error(f"Ошибка подключения: {msg}")
                return False, f"Ошибка подключения: {msg}"  # <-- ВОЗВРАЩАЕМ СТРОКУ, НЕ СПИСОК!
            
            # Переходим в папку
            try:
                self.mail.select(folder)
                self.logger.debug(f"Перешли в папку {folder}")
            except Exception as e:
                self.logger.error(f"Папка {folder} не найдена: {str(e)}")
                self.disconnect()
                return False, f"Папка {folder} не найдена"
            
            # Ищем все письма
            result, data = self.mail.search(None, 'ALL')
            if result != 'OK':
                self.logger.warning("Нет писем в папке")
                self.disconnect()
                return True, []  # Пустой список, но без ошибки!
            
            backups = []
            for num in data[0].split():
                try:
                    result, data = self.mail.fetch(num, '(RFC822)')
                    if result == 'OK':
                        email_body = data[0][1]
                        message = email.message_from_bytes(email_body)
                        
                        # Получаем информацию
                        subject = message['subject']
                        date = message['date']
                        
                        # Ищем вложение
                        has_attachment = False
                        filename = None
                        for part in message.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get('Content-Disposition'):
                                has_attachment = True
                                filename = part.get_filename()
                                break
                        
                        if has_attachment:
                            backups.append({
                                'id': num.decode(),
                                'subject': subject,
                                'date': date,
                                'filename': filename
                            })
                except Exception as e:
                    self.logger.error(f"Ошибка обработки письма {num}: {str(e)}")
                    continue
            
            self.disconnect()
            self.logger.info(f"Найдено {len(backups)} бэкапов")
            return True, backups  # <-- ВОЗВРАЩАЕМ True И СПИСОК
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка: {str(e)}")
            self.disconnect()
            return False, str(e)  # <-- ВОЗВРАЩАЕМ СТРОКУ С ОШИБКОЙ
    
    def download_backup(self, email, password, backup_id, folder='GameVault_Backups'):
        """Скачивание бэкапа из облака"""
        self.logger.info(f"Скачивание бэкапа ID {backup_id} из папки {folder}")
        
        try:
            success, msg = self.connect_imap(email, password)
            if not success:
                self.logger.error(f"Ошибка подключения: {msg}")
                return False, None
            
            self.mail.select(folder)
            result, data = self.mail.fetch(backup_id, '(RFC822)')
            
            if result != 'OK':
                self.logger.error(f"Не удалось получить письмо {backup_id}")
                self.disconnect()
                return False, None
            
            message = email.message_from_bytes(data[0][1])
            
            # Ищем вложение
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition'):
                    filename = part.get_filename()
                    if filename and filename.startswith('backup_'):
                        # Сохраняем в локальную папку
                        local_path = os.path.join('backups', 'cloud_' + filename)
                        os.makedirs('backups', exist_ok=True)
                        
                        with open(local_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        self.disconnect()
                        self.logger.info(f"Бэкап сохранен как {local_path}")
                        return True, local_path
            
            self.disconnect()
            self.logger.warning(f"В письме {backup_id} не найдено вложение")
            return False, None
            
        except Exception as e:
            self.logger.error(f"Ошибка при скачивании: {str(e)}")
            self.disconnect()
            return False, None
    
    def delete_backup(self, email, password, backup_id, folder='GameVault_Backups'):
        """Удаление бэкапа из облака"""
        self.logger.info(f"Удаление бэкапа ID {backup_id} из папки {folder}")
        
        try:
            success, msg = self.connect_imap(email, password)
            if not success:
                self.logger.error(f"Ошибка подключения: {msg}")
                return False, msg
            
            self.mail.select(folder)
            self.mail.store(backup_id, '+FLAGS', '\\Deleted')
            self.mail.expunge()
            
            self.disconnect()
            self.logger.info("Бэкап успешно удален")
            return True, "Бэкап удален"
            
        except Exception as e:
            self.logger.error(f"Ошибка при удалении: {str(e)}")
            self.disconnect()
            return False, str(e)
    
    def test_connection(self, email, password):
        """Тест подключения к облаку"""
        self.logger.info(f"Тест подключения для {email}")
        return self.connect_imap(email, password)