"""
Data Table Widget — Sortable, filterable table for displaying system data.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QWidget, QLineEdit, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import Any


class DataTable(QWidget):
    """A sortable data table with optional search filter."""

    def __init__(self, columns: list[str], searchable: bool = True, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._all_data: list[list[str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search bar
        if searchable:
            search_row = QHBoxLayout()
            search_icon = QLabel("🔍")
            search_row.addWidget(search_icon)
            self._search = QLineEdit()
            self._search.setPlaceholderText("Filter...")
            self._search.textChanged.connect(self._filter)
            search_row.addWidget(self._search)
            layout.addLayout(search_row)
        else:
            self._search = None

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(columns)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        self._table.setSortingEnabled(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

    def set_data(self, rows: list[list[str]]):
        """Replace all table data with new rows."""
        self._all_data = rows
        self._populate(rows)

    def _populate(self, rows: list[list[str]]):
        """Fill the table with rows."""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                item = QTableWidgetItem(str(cell))
                # Try numeric sorting for numeric-looking values
                try:
                    num = float(cell.replace("%", "").replace(",", ""))
                    item.setData(Qt.ItemDataRole.UserRole, num)
                except (ValueError, AttributeError):
                    pass
                self._table.setItem(r, c, item)
        self._table.setSortingEnabled(True)

    def _filter(self, text: str):
        """Filter rows based on search text."""
        if not text:
            self._populate(self._all_data)
            return

        text_lower = text.lower()
        filtered = [
            row for row in self._all_data
            if any(text_lower in str(cell).lower() for cell in row)
        ]
        self._populate(filtered)

    def clear(self):
        """Clear all data."""
        self._all_data = []
        self._table.setRowCount(0)
