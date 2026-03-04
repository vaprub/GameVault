# gui/login_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger('GameVault.LoginDialog')


class LoginDialog(QDialog):
    def __init__(self, database, crypto):
        super().__init__()
        self.database = database
        self.crypto = crypto
        self.config = {}  # Будет заполнено после успешного входа
        self.setWindowTitle("Вход в GameVault")
        self.setModal(True)

        layout = QVBoxLayout()

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.try_login)
        layout.addWidget(QLabel("Мастер-пароль:"))
        layout.addWidget(self.password_edit)

        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self.try_login)
        layout.addWidget(self.login_btn)

        # Если хранилище не инициализировано, показываем кнопку "Создать"
        if not self.crypto.is_initialized():
            self.create_btn = QPushButton("Создать новое хранилище")
            self.create_btn.clicked.connect(self.create_new_vault)
            layout.addWidget(self.create_btn)

        self.setLayout(layout)

    def create_new_vault(self):
        """Создание нового хранилища (первый запуск)."""
        password = self.password_edit.text()
        if len(password) < 6:
            QMessageBox.warning(self, "Слабый пароль", "Пароль должен быть не менее 6 символов.")
            return

        # Подтверждение пароля
        confirm, ok = QInputDialog.getText(self, "Подтверждение", "Повторите пароль:", QLineEdit.EchoMode.Password)
        if not ok or confirm != password:
            QMessageBox.critical(self, "Ошибка", "Пароли не совпадают.")
            return

        try:
            self.crypto.create_new_vault(password)
            # Теперь можно разблокировать
            self.crypto.unlock_vault(password)  # на самом деле ключ уже есть, но для единообразия
            self.database.crypto = self.crypto
            self.database.load()  # загрузит пустой список
            self.config['salt'] = self.crypto.salt
            self.accept()
        except Exception as e:
            logger.exception("Failed to create new vault")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать хранилище: {e}")

    def try_login(self):
        """Попытка входа в существующее хранилище."""
        password = self.password_edit.text()
        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль.")
            return

        try:
            # Проверяем, инициализировано ли хранилище
            if not self.crypto.is_initialized():
                QMessageBox.critical(self, "Ошибка", "Хранилище не инициализировано. Создайте новое.")
                return

            self.crypto.unlock_vault(password)
            self.database.crypto = self.crypto
            self.database.load()  # попытка расшифровки данных
            self.config['salt'] = self.crypto.salt
            self.accept()
        except Exception as e:
            logger.warning(f"Login failed: {e}")
            QMessageBox.critical(self, "Ошибка", "Неверный пароль или повреждённые данные.")
