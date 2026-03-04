# gui/add_account.py
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from core.crypto import CryptoManager

logger = logging.getLogger('GameVault.GUI.AddAccount')

class AddAccountDialog(QDialog):
    """Диалог добавления/редактирования аккаунта"""
    
    def __init__(self, parent=None, account=None):
        super().__init__(parent)
        self.account = account or {}
        self.crypto = CryptoManager()
        self.init_ui()
        logger.debug("AddAccountDialog инициализирован")
        
    def init_ui(self):
        self.setWindowTitle("Добавление аккаунта" if not self.account else "Редактирование аккаунта")
        self.setFixedSize(500, 450)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Игра
        layout.addWidget(QLabel("Название игры:"))
        self.game_input = QLineEdit()
        self.game_input.setText(self.account.get('game', ''))
        self.game_input.setPlaceholderText("Например: World of Warcraft")
        layout.addWidget(self.game_input)
        
        # Логин
        layout.addWidget(QLabel("Логин/Email:"))
        self.login_input = QLineEdit()
        self.login_input.setText(self.account.get('login', ''))
        layout.addWidget(self.login_input)
        
        # Пароль
        layout.addWidget(QLabel("Пароль:"))
        password_layout = QHBoxLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setText(self.account.get('password', ''))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(30, 30)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)
        
        self.generate_btn = QPushButton("🎲 Сгенерировать")
        self.generate_btn.clicked.connect(self.generate_password)
        password_layout.addWidget(self.generate_btn)
        
        layout.addLayout(password_layout)
        
        # Привязанная почта
        layout.addWidget(QLabel("Привязанная почта (необязательно):"))
        self.email_input = QLineEdit()
        self.email_input.setText(self.account.get('email', ''))
        self.email_input.setPlaceholderText("email@example.com")
        layout.addWidget(self.email_input)
        
        # Пароль от почты
        layout.addWidget(QLabel("Пароль от почты (необязательно):"))
        self.email_password_input = QLineEdit()
        self.email_password_input.setText(self.account.get('email_password', ''))
        self.email_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.email_password_input)
        
        # Заметки
        layout.addWidget(QLabel("Заметки:"))
        self.notes_input = QLineEdit()
        self.notes_input.setText(self.account.get('notes', ''))
        layout.addWidget(self.notes_input)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def toggle_password_visibility(self, checked):
        """Показать/скрыть пароль"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def generate_password(self):
        """Генерация пароля"""
        password = self.crypto.generate_password()
        self.password_input.setText(password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        self.show_password_btn.setChecked(True)
        QMessageBox.information(self, "Пароль сгенерирован", 
                               f"Пароль: {password}\n\nСкопируйте его сейчас!")
        logger.info("Сгенерирован новый пароль")
    
    def get_account(self):
        """Получить данные аккаунта"""
        return {
            'game': self.game_input.text().strip(),
            'login': self.login_input.text().strip(),
            'password': self.password_input.text().strip(),
            'email': self.email_input.text().strip(),
            'email_password': self.email_password_input.text().strip(),
            'notes': self.notes_input.text().strip()
        }
