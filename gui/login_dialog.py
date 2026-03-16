# gui/login_dialog.py
import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal

logger = logging.getLogger('GameVault.GUI.Login')

class LoginDialog(QDialog):
    """Диалог входа/регистрации (работает с новой SQLite БД)."""

    login_successful = pyqtSignal(object, object)  # database, config

    def __init__(self, database, crypto):
        super().__init__()
        self.database = database
        self.crypto = crypto
        self.config = {}  # здесь можно хранить настройки, но пока не используется
        self.init_ui()
        logger.debug("LoginDialog инициализирован")

    def init_ui(self):
        self.setWindowTitle("GameVault - Вход")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #3c3c3c;
                border-radius: 5px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#primary {
                background-color: #0078d4;
                color: white;
            }
            QPushButton#primary:hover {
                background-color: #005a9e;
            }
            QPushButton#secondary {
                background-color: #3c3c3c;
                color: white;
            }
            QPushButton#secondary:hover {
                background-color: #4c4c4c;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("🎮 GameVault")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d4;")
        layout.addWidget(title)

        # Подзаголовок – определяем, новый это пользователь или существующий
        self.is_new_user = not self.crypto.is_initialized()
        if self.is_new_user:
            subtitle = QLabel("Создайте новое хранилище")
        else:
            subtitle = QLabel("Введите мастер-пароль")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #888888; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # Email (только для нового хранилища – необязательно)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email для восстановления (необязательно)")
        self.email_input.hide()
        layout.addWidget(self.email_input)

        # Пароль
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Мастер-пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.login_btn = QPushButton("Войти" if not self.is_new_user else "Создать")
        self.login_btn.setObjectName("primary")
        self.login_btn.clicked.connect(self.handle_login)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # Информация
        info = QLabel("⚠️ Мастер-пароль невозможно восстановить без email")
        info.setStyleSheet("color: #888888; font-size: 12px;")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        self.setLayout(layout)

        # Для нового пользователя показываем поле email
        if self.is_new_user:
            self.email_input.show()
            self.login_btn.setText("Создать")

    def handle_login(self):
        password = self.password_input.text()
        email = self.email_input.text() if self.email_input.isVisible() else None

        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите мастер-пароль")
            return

        if self.is_new_user:
            # Создание нового хранилища
            logger.info("Создание нового хранилища")
            try:
                self.crypto.create_new_vault(password)
                # База данных уже создана автоматически при инициализации self.database
                # Сохраняем email в конфигурацию (можно добавить позже в таблицу настроек)
                # Пока просто пропускаем
                logger.info("Хранилище создано")
                self.login_successful.emit(self.database, self.config)
                self.accept()
            except Exception as e:
                logger.error(f"Ошибка создания хранилища: {e}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать хранилище: {e}")
        else:
            # Вход в существующее хранилище
            logger.info("Попытка входа в существующее хранилище")
            try:
                self.crypto.unlock_vault(password)
                logger.info("Успешный вход")
                self.login_successful.emit(self.database, self.config)
                self.accept()
            except Exception as e:
                logger.warning(f"Неверный пароль: {e}")
                QMessageBox.warning(self, "Ошибка", "Неверный мастер-пароль!")