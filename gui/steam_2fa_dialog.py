# gui/steam_2fa_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout

class Steam2FADialog(QDialog):
    """Простой диалог для ввода кода двухфакторной аутентификации Steam."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Steam Guard")
        self.setFixedSize(350, 180)
        self.code = None

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Для синхронизации Steam требуется код подтверждения.\n"
                       "Введите код из приложения Steam Guard или из email:")
        label.setWordWrap(True)
        layout.addWidget(label)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("код")
        layout.addWidget(self.code_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_ok(self):
        self.code = self.code_edit.text().strip()
        if self.code:
            self.accept()
        else:
            self.code_edit.setFocus()