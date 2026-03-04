# gui/password_dialog.py
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                            QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt

logger = logging.getLogger('GameVault.GUI.Password')

class PasswordDialog(QDialog):
    """Диалог ввода пароля"""
    
    def __init__(self, prompt, parent=None, is_new=False):
        super().__init__(parent)
        self.prompt = prompt
        self.is_new = is_new
        self.password = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Ввод пароля")
        self.setFixedSize(400, 200 if not self.is_new else 250)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Подсказка
        label = QLabel(self.prompt)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Поле ввода
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        if self.is_new:
            # Подтверждение пароля
            label2 = QLabel("Подтвердите пароль:")
            label2.setWordWrap(True)
            layout.addWidget(label2)
            
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.confirm_input)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.validate)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def validate(self):
        """Проверка пароля"""
        password = self.password_input.text()
        
        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            return
        
        if self.is_new:
            confirm = self.confirm_input.text()
            
            if len(password) < 6:
                QMessageBox.warning(self, "Ошибка", 
                                   "Пароль должен быть не менее 6 символов")
                return
            
            if password != confirm:
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return
        
        self.password = password
        self.accept()
    
    def get_password(self):
        """Получить пароль"""
        return self.password
