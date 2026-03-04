# core/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name=None):
    """Настройка логирования для всех модулей"""
    
    # Создаем папку для логов если нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Корневой логгер
    logger = logging.getLogger(name) if name else logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Если у логгера уже есть обработчики - не добавляем повторно
    if not logger.handlers:
        # Файловый handler с ротацией
        file_handler = RotatingFileHandler(
            'logs/gamevault.log',
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Формат для файла
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Консольный handler (только ошибки)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

# Создаем логгеры для каждого модуля
root_logger = setup_logger()
core_logger = logging.getLogger('GameVault.Core')
gui_logger = logging.getLogger('GameVault.GUI')
cloud_logger = logging.getLogger('GameVault.Cloud')
db_logger = logging.getLogger('GameVault.Database')
