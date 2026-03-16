# gui/games_dialog.py
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QInputDialog, QLineEdit, QLabel,
                             QSpinBox, QComboBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

logger = logging.getLogger('GameVault.GUI.Games')

class EditGameDialog(QDialog):
    """Диалог добавления/редактирования игры."""
    def __init__(self, parent=None, game_data=None):
        super().__init__(parent)
        self.game_data = game_data or {}
        self.setWindowTitle("Добавить игру" if not game_data else "Редактировать игру")
        self.setFixedSize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setText(self.game_data.get('game_name', ''))
        layout.addRow("Название игры:", self.name_edit)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Steam", "Xbox", "PlayStation", "Epic", "Battle.net", "Ubisoft", "Другое"])
        current_platform = self.game_data.get('game_platform', '')
        index = self.platform_combo.findText(current_platform)
        if index >= 0:
            self.platform_combo.setCurrentIndex(index)
        layout.addRow("Платформа:", self.platform_combo)

        self.playtime_spin = QSpinBox()
        self.playtime_spin.setRange(0, 999999)
        self.playtime_spin.setValue(self.game_data.get('playtime', 0))
        layout.addRow("Время (часы):", self.playtime_spin)

        self.appid_edit = QLineEdit()
        self.appid_edit.setText(str(self.game_data.get('appid', '')))
        self.appid_edit.setPlaceholderText("Steam AppID (если есть)")
        layout.addRow("AppID:", self.appid_edit)

        self.last_played_edit = QLineEdit()
        self.last_played_edit.setText(self.game_data.get('last_played', ''))
        self.last_played_edit.setPlaceholderText("Дата последней игры")
        layout.addRow("Последняя игра:", self.last_played_edit)

        # Кнопки
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def get_data(self):
        return {
            'game_name': self.name_edit.text().strip(),
            'game_platform': self.platform_combo.currentText(),
            'playtime': self.playtime_spin.value(),
            'appid': self.appid_edit.text().strip(),
            'last_played': self.last_played_edit.text().strip()
        }

class GamesDialog(QDialog):
    """Диалог для просмотра и редактирования игр аккаунта."""
    def __init__(self, database, account_id, parent=None):
        super().__init__(parent)
        self.database = database
        self.account_id = account_id
        self.account = database.get_account(account_id)
        self.setWindowTitle(f"Игры аккаунта {self.account['login']} ({self.account['platform']})")
        self.setMinimumSize(800, 400)
        self.init_ui()
        self.load_games()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Таблица игр
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Название", "Платформа", "Время (часы)", "Последняя игра", "AppID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_game)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_game)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_game)
        btn_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def load_games(self):
        games = self.database.get_games(self.account_id)
        self.table.setRowCount(len(games))
        for row, game in enumerate(games):
            self.table.setItem(row, 0, QTableWidgetItem(game['game_name']))
            self.table.setItem(row, 1, QTableWidgetItem(game.get('game_platform', '')))
            self.table.setItem(row, 2, QTableWidgetItem(str(game.get('playtime', 0))))
            self.table.setItem(row, 3, QTableWidgetItem(game.get('last_played', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(game.get('appid', ''))))

    def add_game(self):
        dlg = EditGameDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data['game_name']:
                self.database.add_game(self.account_id, data)
                self.load_games()
            else:
                QMessageBox.warning(self, "Ошибка", "Название игры не может быть пустым")

    def edit_game(self):
        current = self.table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите игру")
            return
        games = self.database.get_games(self.account_id)
        game = games[current]
        dlg = EditGameDialog(self, game)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data['game_name']:
                self.database.update_game(game['id'], data)
                self.load_games()
            else:
                QMessageBox.warning(self, "Ошибка", "Название игры не может быть пустым")

    def delete_game(self):
        current = self.table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите игру")
            return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранную игру?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            games = self.database.get_games(self.account_id)
            game_id = games[current]['id']
            self.database.delete_game(game_id)
            self.load_games()