# gui/main_window.py
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QLineEdit, QLabel,
                            QMenuBar, QMenu, QStatusBar, QInputDialog, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QFont, QColor

# Импорты платформ (для синхронизации)
from core.platforms.steam import SteamPlatform, AuthCodeRequired
from core.platforms.psn import PSNPlatform
from core.platforms.xbox import XboxPlatform
from core.platforms.epic import EpicPlatform
from core.platforms.battlenet import BattleNetPlatform
from core.platforms.ubisoft import UbisoftPlatform
from .steam_2fa_dialog import Steam2FADialog
from .games_dialog import GamesDialog  # новый диалог

logger = logging.getLogger('GameVault.GUI.Main')

class MainWindow(QMainWindow):
    """Главное окно программы"""
    
    def __init__(self, database, config):
        super().__init__()
        self.database = database
        self.config = config
        self.init_ui()
        self.load_accounts()
        logger.info("Главное окно инициализировано")
        
    def init_ui(self):
        self.setWindowTitle("GameVault - Менеджер игровых аккаунтов")
        self.setMinimumSize(1200, 600)
        
        # Стили
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #333333;
                color: #ffffff;
                gridline-color: #3c3c3c;
                selection-background-color: #0078d4;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton#danger {
                background-color: #d32f2f;
            }
            QPushButton#danger:hover {
                background-color: #b71c1c;
            }
            QPushButton.table-button {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                padding: 0px;
            }
            QPushButton.table-button:hover {
                background-color: #005a9e;
            }
            QPushButton.table-button#danger {
                background-color: #d32f2f;
            }
            QPushButton.table-button#danger:hover {
                background-color: #b71c1c;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #3c3c3c;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #888888;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Верхняя панель
        top_panel = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по игре, платформе или логину...")
        self.search_input.textChanged.connect(self.search_accounts)
        top_panel.addWidget(self.search_input)
        
        self.add_btn = QPushButton("➕ Добавить аккаунт")
        self.add_btn.clicked.connect(self.add_account)
        top_panel.addWidget(self.add_btn)
        
        self.backup_btn = QPushButton("💾 Бэкапы")
        self.backup_btn.clicked.connect(self.show_backups)
        top_panel.addWidget(self.backup_btn)
        
        self.cloud_btn = QPushButton("☁️ Облако")
        self.cloud_btn.clicked.connect(self.show_cloud)
        top_panel.addWidget(self.cloud_btn)
        
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.settings_btn.clicked.connect(self.show_settings)
        top_panel.addWidget(self.settings_btn)
        
        self.sync_btn = QPushButton("🔄 Синхронизировать игры")
        self.sync_btn.clicked.connect(self.sync_selected_account)
        top_panel.addWidget(self.sync_btn)
        
        layout.addLayout(top_panel)
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(self.stats_label)
        
        # Таблица аккаунтов (теперь 7 колонок, последняя - кнопка "Игры")
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Платформа", "Логин", "Пароль", "Почта", "Кол-во игр", "Действия"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Платформа
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Логин
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Пароль
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Почта
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Кол-во игр
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Действия
        
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        self.create_menu()
        self.statusBar().showMessage("Готово")
        
    def create_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        backup_action = QAction("Создать бэкап", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        cloud_action = QAction("Облачное хранилище", self)
        cloud_action.triggered.connect(self.show_cloud)
        file_menu.addAction(cloud_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        accounts_menu = menubar.addMenu("Аккаунты")
        add_action = QAction("Добавить", self)
        add_action.triggered.connect(self.add_account)
        accounts_menu.addAction(add_action)
        
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.load_accounts)
        accounts_menu.addAction(refresh_action)
        
        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def load_accounts(self):
        """Загрузка аккаунтов в таблицу"""
        self.table.setRowCount(0)
        accounts = self.database.get_accounts()
        
        if not accounts:
            self.stats_label.setText("📊 Всего аккаунтов: 0")
            return
        
        sorted_accounts = sorted(accounts, key=lambda a: (a['platform'], a['login']))
        
        for row, acc in enumerate(sorted_accounts):
            self.table.insertRow(row)
            
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(acc['id'])))
            
            # Платформа
            self.table.setItem(row, 1, QTableWidgetItem(acc['platform']))
            
            # Логин
            self.table.setItem(row, 2, QTableWidgetItem(acc['login']))
            
            # Пароль
            password_item = QTableWidgetItem(acc['password'])
            password_item.setForeground(QColor("#0078d4"))
            self.table.setItem(row, 3, password_item)
            
            # Почта
            email = acc.get('email', '')
            if email:
                email_item = QTableWidgetItem(f"{email}\n({acc.get('email_password', '***')})")
            else:
                email_item = QTableWidgetItem("")
            self.table.setItem(row, 4, email_item)
            
            # Количество игр
            games = self.database.get_games(acc['id'])
            self.table.setItem(row, 5, QTableWidgetItem(str(len(games))))
            
            # Кнопки действий (редактировать, удалить, игры)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 32)
            edit_btn.setProperty("class", "table-button")
            edit_btn.setToolTip("Редактировать")
            edit_btn.clicked.connect(lambda checked, aid=acc['id']: self.edit_account(aid))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 32)
            delete_btn.setProperty("class", "table-button")
            delete_btn.setObjectName("danger")
            delete_btn.setToolTip("Удалить")
            delete_btn.clicked.connect(lambda checked, aid=acc['id']: self.delete_account(aid))
            
            games_btn = QPushButton("🎮")
            games_btn.setFixedSize(32, 32)
            games_btn.setProperty("class", "table-button")
            games_btn.setToolTip("Игры")
            games_btn.clicked.connect(lambda checked, aid=acc['id']: self.show_games_dialog(aid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(games_btn)
            actions_layout.addStretch()
            
            self.table.setCellWidget(row, 6, actions_widget)
        
        self.stats_label.setText(f"📊 Всего аккаунтов: {len(accounts)}")
        logger.debug(f"Загружено {len(accounts)} аккаунтов")
        
    def search_accounts(self):
        """Поиск аккаунтов по логину, платформе, заметкам и названиям игр."""
        query = self.search_input.text()
        if not query:
            self.load_accounts()
            return
        
        results = self.database.search_accounts(query)
        
        self.table.setRowCount(0)
        for row, acc in enumerate(results):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(acc['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(acc['platform']))
            self.table.setItem(row, 2, QTableWidgetItem(acc['login']))
            self.table.setItem(row, 3, QTableWidgetItem(acc['password']))
            
            email = acc.get('email', '')
            if email:
                self.table.setItem(row, 4, QTableWidgetItem(f"{email}"))
            else:
                self.table.setItem(row, 4, QTableWidgetItem(""))
            
            games = self.database.get_games(acc['id'])
            self.table.setItem(row, 5, QTableWidgetItem(str(len(games))))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 32)
            edit_btn.setProperty("class", "table-button")
            edit_btn.clicked.connect(lambda checked, aid=acc['id']: self.edit_account(aid))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 32)
            delete_btn.setProperty("class", "table-button")
            delete_btn.setObjectName("danger")
            delete_btn.clicked.connect(lambda checked, aid=acc['id']: self.delete_account(aid))
            
            games_btn = QPushButton("🎮")
            games_btn.setFixedSize(32, 32)
            games_btn.setProperty("class", "table-button")
            games_btn.clicked.connect(lambda checked, aid=acc['id']: self.show_games_dialog(aid))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addWidget(games_btn)
            actions_layout.addStretch()
            
            self.table.setCellWidget(row, 6, actions_widget)
        
        self.stats_label.setText(f"📊 Найдено: {len(results)}")
        logger.debug(f"Поиск '{query}': найдено {len(results)}")
        
    def add_account(self):
        from .add_account import AddAccountDialog
        dialog = AddAccountDialog(self)
        if dialog.exec():
            account = dialog.get_account()
            self.database.add_account(account)
            self.load_accounts()
            self.statusBar().showMessage("✅ Аккаунт добавлен")
            logger.info(f"Добавлен аккаунт: {account.get('game')}")
    
    def edit_account(self, account_id):
        from .add_account import AddAccountDialog
        account = self.database.get_account(account_id)
        if not account:
            return
        dialog = AddAccountDialog(self, account)
        if dialog.exec():
            updated = dialog.get_account()
            if 'id' in updated:
                del updated['id']
            self.database.update_account(account_id, updated)
            self.load_accounts()
            self.statusBar().showMessage("✅ Аккаунт обновлен")
            logger.info(f"Обновлен аккаунт ID: {account_id}")
    
    def delete_account(self, account_id):
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этот аккаунт?\nВсе связанные игры будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_account(account_id):
                self.load_accounts()
                self.statusBar().showMessage("🗑️ Аккаунт удален")
                logger.info(f"Удален аккаунт ID: {account_id}")
    
    def show_backups(self):
        from .backups import BackupsDialog
        dialog = BackupsDialog(self.database, self)
        if dialog.exec():
            self.load_accounts()
    
    def show_cloud(self):
        from .cloud_backups import CloudBackupsDialog
        dialog = CloudBackupsDialog(self.database, self.config, self)
        dialog.exec()
    
    def show_settings(self):
        from .settings import SettingsDialog
        dialog = SettingsDialog(self.database, self.config, self)
        if dialog.exec():
            self.config = dialog.get_config()
    
    def create_backup(self):
        backup_file = self.database.create_backup()
        if backup_file:
            self.statusBar().showMessage(f"✅ Бэкап создан: {backup_file}")
            logger.info(f"Бэкап создан: {backup_file}")
        else:
            self.statusBar().showMessage("❌ Ошибка создания бэкапа")
            logger.error("Ошибка создания бэкапа")
    
    def show_about(self):
        QMessageBox.about(
            self, "О программе",
            "🎮 GameVault v1.0\n\n"
            "Безопасный менеджер игровых аккаунтов\n"
            "С шифрованием AES-256 и облачным хранением\n\n"
            "© 2024 GameVault"
        )
    
    # ========== МЕТОДЫ ДЛЯ ИГР ==========
    
    def show_games_dialog(self, account_id):
        dialog = GamesDialog(self.database, account_id, self)
        dialog.exec()
        # После закрытия обновляем количество игр в таблице
        self.load_accounts()
    
    def show_games(self, account_id):
        """Старый метод, оставлен для совместимости, но теперь используем диалог."""
        self.show_games_dialog(account_id)
    
    # ========== МЕТОДЫ ДЛЯ СИНХРОНИЗАЦИИ (оставляем как есть) ==========
    def sync_selected_account(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите аккаунт из списка")
            return
        
        account_id = int(self.table.item(selected, 0).text())
        account = self.database.get_account(account_id)
        if not account:
            return
        
        platform_name = account['platform'].lower()
        
        if platform_name == 'steam':
            from core.platforms.steam import SteamPlatform, AuthCodeRequired
            platform = SteamPlatform(self.database, self.database.crypto)
        elif platform_name == 'playstation':
            from core.platforms.psn import PSNPlatform
            platform = PSNPlatform(self.database, self.database.crypto)
        elif platform_name == 'xbox':
            from core.platforms.xbox import XboxPlatform
            platform = XboxPlatform(self.database, self.database.crypto)
        elif platform_name == 'epic games':
            from core.platforms.epic import EpicPlatform
            platform = EpicPlatform(self.database, self.database.crypto)
        elif platform_name == 'battle.net':
            from core.platforms.battlenet import BattleNetPlatform
            platform = BattleNetPlatform(self.database, self.database.crypto)
        elif platform_name == 'ubisoft':
            from core.platforms.ubisoft import UbisoftPlatform
            platform = UbisoftPlatform(self.database, self.database.crypto)
        else:
            QMessageBox.warning(self, "Ошибка", f"Платформа {account['platform']} пока не поддерживается")
            return
        
        if platform_name == 'steam':
            try:
                if platform.authenticate(account_id):
                    logger.info("Steam login successful without code")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось войти в Steam")
                    return
            except AuthCodeRequired as e:
                dlg = Steam2FADialog(self)
                if dlg.exec() == QDialog.Accepted:
                    code = dlg.code
                    try:
                        if platform.authenticate(account_id, code=code, is_2fa=e.is_2fa):
                            logger.info("Steam login successful with code")
                        else:
                            QMessageBox.warning(self, "Ошибка", "Неверный код")
                            return
                    except AuthCodeRequired as e2:
                        QMessageBox.warning(self, "Ошибка", "Неверный код")
                        return
                    except Exception as e2:
                        logger.exception("Steam login error")
                        QMessageBox.critical(self, "Ошибка", f"Ошибка входа: {e2}")
                        return
                else:
                    return
            except Exception as e:
                logger.exception("Steam sync error")
                QMessageBox.critical(self, "Ошибка", f"Ошибка синхронизации: {e}")
                return

            try:
                games = platform.fetch_games(account_id)
                logger.info(f"Получено {len(games)} игр от Steam")
                self.database.delete_all_games(account_id)
                for game in games:
                    self.database.add_game(account_id, game)
                QMessageBox.information(self, "Успех", f"Синхронизировано и сохранено {len(games)} игр")
                self.show_games_dialog(account_id)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка получения списка игр: {e}")
            return
        
        QMessageBox.information(self, "Инфо", f"Синхронизация для {account['platform']} ещё не реализована")