"""
Status Card Widget — Displays a single metric with label, value, and optional unit.
Used throughout all Arcwyre modules for consistent data display.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class StatusCard(QFrame):
    """A card displaying a metric value with title and optional unit/status."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        unit: str = "",
        status: str = "",  # "ok", "warning", "error", or ""
        theme_color: str = "", # Optional hex color to make the stat visually distinct
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        
        # Apple tier drop shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setObjectName("card_title")
        layout.addWidget(self._title_label)

        # Value row
        value_row = QHBoxLayout()
        value_row.setSpacing(6)
        value_row.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("card_value")
        if theme_color:
            self._value_label.setStyleSheet(f"color: {theme_color}; font-size: 32px;")
        else:
            self._value_label.setStyleSheet(f"font-size: 32px;")
            
        value_row.addWidget(self._value_label)

        if unit:
            self._unit_label = QLabel(unit)
            self._unit_label.setObjectName("card_unit")
            value_row.addWidget(self._unit_label, alignment=Qt.AlignmentFlag.AlignBottom)
        else:
            self._unit_label = None

        value_row.addStretch()

        # Status indicator
        self._status_label = QLabel()
        self._status_label.setObjectName(f"status_{status}" if status else "card_unit")
        if status == "ok":
            self._status_label.setText("● Healthy")
        elif status == "warning":
            self._status_label.setText("● Warning")
        elif status == "error":
            self._status_label.setText("● Error")
        value_row.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(value_row)

    def set_value(self, value: str, status: str = ""):
        """Update the displayed value and optionally the status."""
        self._value_label.setText(value)
        if status:
            self._status_label.setObjectName(f"status_{status}")
            status_text = {"ok": "● Healthy", "warning": "● Warning", "error": "● Error"}
            self._status_label.setText(status_text.get(status, ""))
            # Force style refresh
            self._status_label.style().unpolish(self._status_label)
            self._status_label.style().polish(self._status_label)

    def set_title(self, title: str):
        """Update the card title."""
        self._title_label.setText(title)


class InfoRow(QFrame):
    """A simple key-value row for displaying labeled information."""

    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self._label = QLabel(label)
        self._label.setObjectName("card_unit")
        self._label.setMinimumWidth(140)
        layout.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setObjectName("card_title")
        self._value.setWordWrap(True)
        layout.addWidget(self._value, stretch=1)

    def set_value(self, value: str):
        """Update the displayed value."""
        self._value.setText(value)


class SectionHeader(QLabel):
    """A section header label with bottom border styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("section_header")


class NotImplementedLabel(QLabel):
    """
    Standard label for features that are NOT IMPLEMENTED.
    Per directive: never fake success — explain why instead.
    """

    def __init__(self, reason: str, parent=None):
        super().__init__(f"NOT IMPLEMENTED — {reason}", parent)
        self.setObjectName("not_implemented")
        self.setWordWrap(True)
