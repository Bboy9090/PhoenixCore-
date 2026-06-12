"""
Error Dialog — User-friendly error display.
Per directive: every error must explain the problem, cause, and fix.
No cryptic stack traces.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit
from PyQt6.QtCore import Qt

from arcwyre.theme import COLORS


class ErrorDialog(QDialog):
    """
    User-friendly error dialog.
    Shows: What happened, Why it happened, How to fix it.
    """

    def __init__(
        self,
        title: str,
        problem: str,
        cause: str,
        fix: str,
        details: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Arcwyre — {title}")
        self.setMinimumWidth(480)
        self.setMaximumWidth(640)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Icon + Title
        title_label = QLabel(f"⚠  {title}")
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['warning']};
        """)
        layout.addWidget(title_label)

        # Problem
        problem_header = QLabel("What happened:")
        problem_header.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase;")
        layout.addWidget(problem_header)
        problem_text = QLabel(problem)
        problem_text.setWordWrap(True)
        problem_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; padding-left: 8px;")
        layout.addWidget(problem_text)

        # Cause
        cause_header = QLabel("Why it happened:")
        cause_header.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase;")
        layout.addWidget(cause_header)
        cause_text = QLabel(cause)
        cause_text.setWordWrap(True)
        cause_text.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px; padding-left: 8px;")
        layout.addWidget(cause_text)

        # Fix
        fix_header = QLabel("How to fix it:")
        fix_header.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; text-transform: uppercase;")
        layout.addWidget(fix_header)
        fix_text = QLabel(fix)
        fix_text.setWordWrap(True)
        fix_text.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; padding-left: 8px;")
        layout.addWidget(fix_text)

        # Technical details (collapsible)
        if details:
            details_label = QLabel("Technical Details:")
            details_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            layout.addWidget(details_label)

            details_edit = QTextEdit()
            details_edit.setPlainText(details)
            details_edit.setReadOnly(True)
            details_edit.setMaximumHeight(100)
            details_edit.setStyleSheet(f"""
                background-color: {COLORS['panel']};
                color: {COLORS['text_dim']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-family: monospace;
                font-size: 11px;
            """)
            layout.addWidget(details_edit)

        # OK button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary_button")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)


class ConfirmationDialog(QDialog):
    """
    Safety confirmation dialog for destructive operations.
    Requires explicit confirmation before proceeding.
    """

    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_dangerous: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Arcwyre — {title}")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Icon
        icon_color = COLORS['danger'] if is_dangerous else COLORS['warning']
        icon = "⛔" if is_dangerous else "⚠"
        title_label = QLabel(f"{icon}  {title}")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {icon_color};")
        layout.addWidget(title_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 13px;")
        layout.addWidget(msg_label)

        if detail:
            detail_label = QLabel(detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
            layout.addWidget(detail_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("danger_button" if is_dangerous else "primary_button")
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

        self._confirmed = False

    @staticmethod
    def confirm(title, message, detail="", confirm_text="Confirm",
                cancel_text="Cancel", is_dangerous=False, parent=None) -> bool:
        """Static method to show confirmation and return True if confirmed."""
        dlg = ConfirmationDialog(
            title, message, detail, confirm_text, cancel_text, is_dangerous, parent
        )
        return dlg.exec() == QDialog.DialogCode.Accepted
