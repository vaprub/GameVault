# gui/backups.py
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QListWidget, QListWidgetItem,
                            QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
import os

logger = logging.getLogger('GameVault.GUI.Backups')

class BackupsDialog(QDialog):
    """Диалог управления бэкапами"""
    
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.init_ui()
        self.load_backups()
        
    def init_ui(self):
        self.setWindowTitle("Управление бэкапами")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Список бэкапов
        group = QGroupBox("📋 Доступные бэкапы")
        group_layout = QVBoxLayout()
        
        self.backup_list = QListWidget()
        self.backup_list.itemDoubleClicked.connect(self.restore_selected)
        group_layout.addWidget(self.backup_list)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.restore_btn = QPushButton("♻️ Восстановить")
        self.restore_btn.clicked.connect(self.restore_selected)
        btn_layout.addWidget(self.restore_btn)
        
        self.create_btn = QPushButton("📦 Создать бэкап")
        self.create_btn.clicked.connect(self.create_backup)
        btn_layout.addWidget(self.create_btn)
        
        self.delete_old_btn = QPushButton("🗑️ Удалить старые")
        self.delete_old_btn.clicked.connect(self.delete_old)
        btn_layout.addWidget(self.delete_old_btn)
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def load_backups(self):
        """Загрузка списка бэкапов"""
        self.backup_list.clear()
        backups = self.database.get_backups()
        
        if not backups:
            item = QListWidgetItem("📭 Нет доступных бэкапов")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.backup_list.addItem(item)
            self.restore_btn.setEnabled(False)
        else:
            for backup in backups:
                text = f"{backup['date']} - {backup['size']} байт"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, backup['path'])
                self.backup_list.addItem(item)
            self.restore_btn.setEnabled(True)
    
    def restore_selected(self):
        """Восстановить выбранный бэкап"""
        current = self.backup_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Ошибка", "Выберите бэкап")
            return
        
        backup_path = current.data(Qt.ItemDataRole.UserRole)
        if not backup_path:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Восстановление из бэкапа заменит текущие данные.\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Создаем бэкап текущего состояния
            self.database.create_backup()
            
            # Восстанавливаем
            if self.database.restore_backup(backup_path):
                QMessageBox.information(
                    self, "Успех",
                    "Бэкап восстановлен!\nПерезапустите программу."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось восстановить бэкап")
    
    def create_backup(self):
        """Создание нового бэкапа"""
        backup_file = self.database.create_backup()
        if backup_file:
            QMessageBox.information(
                self, "Успех",
                f"Бэкап создан:\n{os.path.basename(backup_file)}"
            )
            self.load_backups()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось создать бэкап")
    
    def delete_old(self):
        """Удаление старых бэкапов"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить все бэкапы кроме последних 3?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import os
            backups = sorted([f for f in os.listdir('backups') 
                            if f.startswith('backup_')])
            deleted = 0
            for backup in backups[:-3]:
                os.remove(os.path.join('backups', backup))
                deleted += 1
            
            QMessageBox.information(self, "Успех", f"Удалено {deleted} старых бэкапов")
            self.load_backups()
