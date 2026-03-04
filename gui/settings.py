# gui/settings.py
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from core.email_sender import EmailSender
from .cloud_backups import CloudBackupsDialog
from .password_dialog import PasswordDialog

logger = logging.getLogger('GameVault.GUI.Settings')

class SettingsDialog(QDialog):
    """Диалог настроек"""
    
    def __init__(self, database, config, parent=None):
        super().__init__(parent)
        self.database = database
        self.config = config
        self.email_sender = EmailSender(database.crypto)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Настройки")
        self.setFixedSize(600, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Почта
        email_group = QGroupBox("📧 Настройки почты")
        email_layout = QVBoxLayout()
        
        email_layout.addWidget(QLabel("Email для восстановления:"))
        self.email_input = QLineEdit()
        self.email_input.setText(self.config.get('email', ''))
        email_layout.addWidget(self.email_input)
        
        # Статус пароля
        self.password_status = QLabel()
        self.update_password_status()
        email_layout.addWidget(self.password_status)
        
        # Кнопки для почты
        email_buttons = QHBoxLayout()
        
        self.test_email_btn = QPushButton("📨 Тестовое письмо")
        self.test_email_btn.clicked.connect(self.send_test_email)
        email_buttons.addWidget(self.test_email_btn)
        
        self.update_password_btn = QPushButton("🔑 Обновить пароль")
        self.update_password_btn.clicked.connect(self.update_email_password)
        email_buttons.addWidget(self.update_password_btn)
        
        self.clear_password_btn = QPushButton("🗑️ Удалить пароль")
        self.clear_password_btn.clicked.connect(self.clear_email_password)
        email_buttons.addWidget(self.clear_password_btn)
        
        email_layout.addLayout(email_buttons)
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        # Облачное хранилище
        cloud_group = QGroupBox("☁️ Облачное хранилище")
        cloud_layout = QVBoxLayout()
        
        self.cloud_status = QLabel()
        self.update_cloud_status()
        cloud_layout.addWidget(self.cloud_status)
        
        self.cloud_btn = QPushButton("☁️ Управление облаком")
        self.cloud_btn.clicked.connect(self.open_cloud)
        cloud_layout.addWidget(self.cloud_btn)
        
        cloud_group.setLayout(cloud_layout)
        layout.addWidget(cloud_group)
        
        # Безопасность
        security_group = QGroupBox("🔐 Безопасность")
        security_layout = QVBoxLayout()
        
        self.change_password_btn = QPushButton("🔄 Сменить мастер-пароль")
        self.change_password_btn.clicked.connect(self.change_master_password)
        security_layout.addWidget(self.change_password_btn)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        layout.addStretch()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def update_password_status(self):
        """Обновить статус пароля"""
        if 'email_password' in self.config:
            self.password_status.setText("✅ Пароль от почты сохранен (зашифрован)")
            self.password_status.setStyleSheet("color: #4caf50;")
        else:
            self.password_status.setText("⚠️ Пароль от почты не сохранен")
            self.password_status.setStyleSheet("color: #ff9800;")
    
    def update_cloud_status(self):
        """Обновить статус облака"""
        if 'cloud' in self.config:
            cloud_email = self.config['cloud'].get('email', '')
            self.cloud_status.setText(f"✅ Подключено: {cloud_email}")
            self.cloud_status.setStyleSheet("color: #4caf50;")
        else:
            self.cloud_status.setText("⚠️ Облако не настроено")
            self.cloud_status.setStyleSheet("color: #ff9800;")
    
    def send_test_email(self):
        """Отправка тестового письма"""
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Ошибка", "Введите email")
            return
        
        # Получаем пароль
        password = None
        if 'email_password' in self.config:
            password = self.database.crypto.decrypt_password(
                self.config['email_password']
            )
        
        if not password:
            dialog = PasswordDialog("Введите пароль от почты:", self)
            if dialog.exec():
                password = dialog.get_password()
            else:
                return
        
        success, msg = self.email_sender.send_email(
            email,
            "Тестовое письмо GameVault",
            "Если вы это читаете, почта работает правильно!",
            password
        )
        
        if success:
            QMessageBox.information(self, "Успех", "Письмо отправлено!")
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось отправить: {msg}")
    
    def update_email_password(self):
        """Обновление пароля от почты"""
        dialog = PasswordDialog("Введите новый пароль от почты:", self)
        if dialog.exec():
            password = dialog.get_password()
            encrypted = self.database.crypto.encrypt_password(password)
            if encrypted:
                self.config['email_password'] = encrypted
                self.database.save_config()
                self.update_password_status()
                QMessageBox.information(self, "Успех", "Пароль сохранен!")
    
    def clear_email_password(self):
        """Очистка пароля от почты"""
        if 'email_password' in self.config:
            del self.config['email_password']
            self.database.save_config()
            self.update_password_status()
            QMessageBox.information(self, "Успех", "Пароль удален!")
    
    def open_cloud(self):
        """Открыть управление облаком"""
        dialog = CloudBackupsDialog(self.database, self.config, self)
        if dialog.exec():
            self.update_cloud_status()
    
    def change_master_password(self):
        """Смена мастер-пароля"""
        # Запрашиваем старый пароль
        old_dialog = PasswordDialog("Введите старый мастер-пароль:", self)
        if not old_dialog.exec():
            return
        old_password = old_dialog.get_password()
        
        # Проверяем старый пароль
        try:
            success, _ = self.database.load_data(old_password)
            if not success:
                QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
                return
        except:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            return
        
        # Запрашиваем новый пароль
        new_dialog = PasswordDialog("Введите новый мастер-пароль:", self, is_new=True)
        if new_dialog.exec():
            new_password = new_dialog.get_password()
            
            # Сохраняем старые данные
            old_data = self.database.data
            old_config = self.database.config.copy()
            
            # Создаем новое хранилище
            success, msg = self.database.create_new_vault(
                new_password,
                old_config.get('email')
            )
            
            if success:
                # Восстанавливаем данные
                self.database.data = old_data
                self.database.config = old_config
                
                # Перешифровываем пароль от почты если есть
                if 'email_password' in self.config:
                    email_password = self.database.crypto.decrypt_password(
                        self.config['email_password']
                    )
                    if email_password:
                        self.config['email_password'] = self.database.crypto.encrypt_password(
                            email_password
                        )
                
                # Перешифровываем облачные пароли если есть
                if 'cloud' in self.config and 'password' in self.config['cloud']:
                    cloud_password = self.database.crypto.decrypt_password(
                        self.config['cloud']['password']
                    )
                    if cloud_password:
                        self.config['cloud']['password'] = self.database.crypto.encrypt_password(
                            cloud_password
                        )
                
                self.database.save_data()
                self.database.save_config()
                
                QMessageBox.information(self, "Успех", "Мастер-пароль изменен!")
            else:
                QMessageBox.warning(self, "Ошибка", msg)
    
    def save_settings(self):
        """Сохранение настроек"""
        email = self.email_input.text().strip()
        if email:
            self.config['email'] = email
        elif 'email' in self.config:
            del self.config['email']
        
        self.database.save_config()
        self.accept()
    
    def get_config(self):
        """Получить обновленную конфигурацию"""
        return self.config
