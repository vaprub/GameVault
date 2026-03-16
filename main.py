#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GameVault - Менеджер игровых аккаунтов
Главный файл запуска (PyQt5 версия)
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

# Импорты PyQt5 (больше никаких PyQt6!)
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QIcon

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

        # Инициализация крипто-менеджера
        self.crypto = CryptoManager()
        self.database = Database(self.crypto)

    def run(self):
        """Запуск приложения"""
        login_dialog = LoginDialog(self.database, self.crypto)

        if login_dialog.exec() == QDialog.Accepted:
            self.main_window = MainWindow(
                login_dialog.database,
                login_dialog.config
            )
            self.main_window.show()
            return self.app.exec()

        return 0


def main():
    app = GameVaultApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()