#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GameVault - Менеджер игровых аккаунтов
Главный файл запуска (исправленная версия)
"""

import os
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('GameVault.Main')


def setup_qt_dll_paths():
    """Однократная настройка путей к DLL PyQt для корректной работы."""
    dll_path = None

    if hasattr(sys, '_MEIPASS'):
        # Режим собранного приложения (PyInstaller)
        base = Path(sys._MEIPASS)
        candidate = base / 'PyQt6' / 'Qt6' / 'bin'
        if candidate.exists():
            dll_path = str(candidate)
    else:
        # Режим разработки – ищем в site-packages
        import site
        for site_path in site.getsitepackages():
            candidate = Path(site_path) / 'PyQt6' / 'Qt6' / 'bin'
            if candidate.exists():
                dll_path = str(candidate)
                break

    if dll_path and os.path.exists(dll_path):
        os.environ['PATH'] = dll_path + os.pathsep + os.environ.get('PATH', '')
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(dll_path)
        logger.info(f"DLL path added: {dll_path}")
    else:
        logger.warning("PyQt6 DLL path not found, application may not start.")


# Вызов настройки путей до импортов PyQt
setup_qt_dll_paths()

# Импорты PyQt и остальных модулей
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Добавляем корневую папку в путь для импорта наших модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import CryptoManager, Database
from gui import LoginDialog, MainWindow


class GameVaultApp:
    """Основной класс приложения"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("GameVault")
        self.app.setApplicationVersion("1.0")

        # Инициализация крипто-менеджера (без пароля, соль будет загружена позже)
        self.crypto = CryptoManager()
        self.database = Database(self.crypto)

    def run(self):
        """Запуск приложения"""
        login_dialog = LoginDialog(self.database, self.crypto)

        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            # Успешный вход – показываем главное окно
            self.main_window = MainWindow(
                login_dialog.database,
                login_dialog.config
            )
            self.main_window.show()
            return self.app.exec()

        return 0


def main():
    """Точка входа"""
    app = GameVaultApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
