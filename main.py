#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GameVault - Менеджер игровых аккаунтов
Главный файл запуска
"""

import os
import sys
import pkgutil

# ПРИНУДИТЕЛЬНАЯ ЗАГРУЗКА DLL ДЛЯ QT
if hasattr(sys, '_MEIPASS'):
    # Путь к DLL внутри собранного EXE
    dll_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'bin')
    if os.path.exists(dll_path):
        os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']
        try:
            os.add_dll_directory(dll_path)
        except AttributeError:
            pass
    print(f"DEBUG: DLL path added: {dll_path}")

# Для обычного запуска через Python
else:
    # Добавляем стандартный путь к DLL PyQt6
    import site
    for path in site.getsitepackages():
        qt_bin = os.path.join(path, 'PyQt6', 'Qt6', 'bin')
        if os.path.exists(qt_bin):
            os.environ['PATH'] = qt_bin + os.pathsep + os.environ['PATH']
            print(f"DEBUG: Added {qt_bin} to PATH")
            break

import sys
import os
from PyQt6.QtWidgets import QApplication
import PyQt6.sip  # Явный импорт для PyInstaller
from PyQt6.QtGui import QIcon
import logging

# Добавляем пути для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import CryptoManager, Database
from gui import LoginDialog, MainWindow
import pkgutil


# Исправление загрузки DLL для PyQt6
import sys
import os
if hasattr(sys, '_MEIPASS'):
    dll_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'bin')
    if os.path.exists(dll_path):
        os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']
        try:
            os.add_dll_directory(dll_path)
        except AttributeError:
            pass


logger = logging.getLogger('GameVault.Main')
class GameVaultApp:
    """Основной класс приложения"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("GameVault")
        self.app.setApplicationVersion("1.0")
        
        # Инициализация ядра
        self.crypto = CryptoManager()
        self.database = Database(self.crypto)
        
    def run(self):
        """Запуск приложения"""
        # Показываем окно входа
        login_dialog = LoginDialog(self.database)
        
        if login_dialog.exec():
            # Успешный вход - показываем главное окно
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