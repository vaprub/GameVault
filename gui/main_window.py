# gui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QLineEdit, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt, QEvent
import logging
import secrets
import string

logger = logging.getLogger('GameVault.MainWindow')


class MainWindow(QMainWindow):
    def __init__(self, database, config):
        super().__init__()
        self.database = database
        self.config = config
        self.setWindowTitle("GameVault")
        self.setGeometry(100, 100, 800, 600)

        # Таймер автоблокировки (5 минут)
        self.inactivity_timer = QTimer()
        self.inactivity_timer.setInterval(5 * 60 * 1000)
        self.inactivity_timer.timeout.connect(self.lock)
        self.inactivity_timer.start()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Таблица аккаунтов
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Email", "Пароль", "Заметка"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_account)
        btn_layout.addWidget(add_btn)

        generate_btn = QPushButton("Сгенерировать пароль")
        generate_btn.clicked.connect(self.generate_password)
        btn_layout.addWidget(generate_btn)

        delete_btn = QPushButton("Удалить выбранное")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh_table)
        btn_layout.addWidget(refresh_btn)

        export_btn = QPushButton("Экспорт")
        export_btn.clicked.connect(self.export_vault)
        btn_layout.addWidget(export_btn)

        import_btn = QPushButton("Импорт")
        import_btn.clicked.connect(self.import_vault)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

        self.refresh_table()

        # Устанавливаем фильтр событий для сброса таймера при любом взаимодействии
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Перехватываем события мыши и клавиатуры для сброса таймера."""
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.Wheel):
            self.inactivity_timer.start()
        return super().eventFilter(obj, event)

    def refresh_table(self):
        accounts = self.database.get_accounts()
        self.table.setRowCount(len(accounts))
        for i, acc in enumerate(accounts):
            self.table.setItem(i, 0, QTableWidgetItem(acc['name']))
            self.table.setItem(i, 1, QTableWidgetItem(acc['email']))
            self.table.setItem(i, 2, QTableWidgetItem(acc['password']))
            self.table.setItem(i, 3, QTableWidgetItem(acc.get('note', '')))

    def add_account(self):
        """Диалог добавления новой записи."""
        name, ok1 = QInputDialog.getText(self, "Добавить запись", "Название:")
        if not ok1 or not name:
            return
        email, ok2 = QInputDialog.getText(self, "Добавить запись", "Email:")
        if not ok2:
            return
        password, ok3 = QInputDialog.getText(self, "Добавить запись", "Пароль:", QLineEdit.EchoMode.Password)
        if not ok3:
            return
        note, ok4 = QInputDialog.getMultiLineText(self, "Добавить запись", "Заметка (необязательно):")
        if not ok4:
            note = ""

        self.database.add_account(name, email, password, note)
        self.refresh_table()
        logger.info(f"Added account: {name}")

    def generate_password(self):
        """Генератор надёжного пароля."""
        length = 16
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Показываем пароль в сообщении
        QMessageBox.information(self, "Сгенерированный пароль",
                                f"Новый пароль:
{password}

Скопируйте его в буфер обмена.")
        # Можно также вставить в поле пароля при добавлении, но для простоты просто показываем

    def delete_selected(self):
        """Удаляет выбранную запись."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Удаление", "Выберите запись для удаления.")
            return

        # Подтверждение
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранную запись?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.database.accounts[current_row]
            self.database.save()
            self.refresh_table()
            logger.info("Deleted selected account.")

    def export_vault(self):
        """Экспорт данных (сохраняет незашифрованную копию – осторожно!)."""
        # В реальном проекте нужно шифровать резервную копию отдельным паролем.
        # Здесь для простоты просто сохраняем открытый JSON.
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить резервную копию", "",
                                                  "JSON Files (*.json)")
        if filename:
            import json
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.database.accounts, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Экспорт", "Резервная копия сохранена.")
                logger.info(f"Exported vault to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def import_vault(self):
        """Импорт данных из резервной копии (заменяет текущие данные)."""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать резервную копию", "",
                                                  "JSON Files (*.json)")
        if filename:
            import json
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                # Простая проверка структуры
                if not isinstance(imported, list):
                    raise ValueError("Неверный формат файла: ожидается список записей.")
                reply = QMessageBox.question(self, "Подтверждение",
                                             "Импорт заменит все текущие записи. Продолжить?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.database.accounts = imported
                    self.database.save()
                    self.refresh_table()
                    logger.info(f"Imported vault from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать: {e}")

    def lock(self):
        """Блокировка приложения (очистка памяти и закрытие окна)."""
        logger.info("Locking due to inactivity.")
        # Очищаем данные в памяти
        self.database.clear_memory()
        # Очищаем таблицу
        self.table.setRowCount(0)
        # Закрываем окно
        self.close()

    def closeEvent(self, event):
        """При закрытии окна тоже очищаем память."""
        self.database.clear_memory()
        event.accept()
