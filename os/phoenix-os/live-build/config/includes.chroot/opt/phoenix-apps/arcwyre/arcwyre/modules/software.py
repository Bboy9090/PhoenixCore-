from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from ..services.package_mgr import PackageManager

class SoftwareModule(QWidget):
    """Arcwyre Software Center Module"""
    
    def __init__(self):
        super().__init__()
        self.pkg_mgr = PackageManager()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40) # Generous Apple-style padding
        layout.setSpacing(24)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Software Center")
        title.setObjectName("title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        if not self.pkg_mgr.is_supported():
            warn_label = QLabel("⚠️ NOT IMPLEMENTED — Requires Debian/Ubuntu-based Linux")
            warn_label.setStyleSheet("color: #ef4444; font-weight: bold; padding: 10px; background-color: rgba(239, 68, 68, 0.1); border-radius: 8px;")
            header_layout.addWidget(warn_label)
            
        layout.addLayout(header_layout)
        
        # Search Box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary")
        search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # Tabs for Installed and Updates
        self.tabs = QTabWidget()
        
        # Installed Tab
        self.installed_tab = QWidget()
        installed_layout = QVBoxLayout(self.installed_tab)
        
        self.installed_table = QTableWidget(0, 3)
        self.installed_table.setHorizontalHeaderLabels(["Package", "Version", "Description"])
        self.installed_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        installed_layout.addWidget(self.installed_table)
        
        refresh_btn = QPushButton("Refresh Installed Packages")
        refresh_btn.setStyleSheet("background-color: #334155; color: white; padding: 8px; border-radius: 4px;")
        refresh_btn.clicked.connect(self._load_installed)
        installed_layout.addWidget(refresh_btn)
        
        self.tabs.addTab(self.installed_tab, "Installed Packages")
        
        # Updates Tab
        self.updates_tab = QWidget()
        updates_layout = QVBoxLayout(self.updates_tab)
        
        self.updates_table = QTableWidget(0, 2)
        self.updates_table.setHorizontalHeaderLabels(["Package", "Details"])
        self.updates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.updates_table.setStyleSheet(self.installed_table.styleSheet())
        updates_layout.addWidget(self.updates_table)
        
        check_updates_btn = QPushButton("Check for Updates")
        check_updates_btn.setStyleSheet("background-color: #334155; color: white; padding: 8px; border-radius: 4px;")
        check_updates_btn.clicked.connect(self._check_updates)
        updates_layout.addWidget(check_updates_btn)
        
        self.tabs.addTab(self.updates_tab, "Available Updates")
        
        # Optional Features Tab (For Windows Compat)
        self.features_tab = QWidget()
        features_layout = QVBoxLayout(self.features_tab)
        features_layout.setSpacing(16)
        
        # Windows Compatibility Card
        from arcwyre.widgets.status_card import StatusCard, InfoRow
        from PyQt6.QtWidgets import QFrame
        from arcwyre.theme import COLORS
        
        win_frame = QFrame()
        win_frame.setObjectName("card")
        win_layout = QVBoxLayout(win_frame)
        
        win_header = QLabel("Windows Diagnostic Layer")
        win_header.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 18px; font-weight: bold;")
        win_layout.addWidget(win_header)
        
        win_desc = QLabel("Installs Wine HQ (~800MB) to allow running lightweight Windows .exe diagnostic tools (Rufus, CPU-Z, BIOS flashers) natively on Arcwyre.")
        win_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        win_desc.setWordWrap(True)
        win_layout.addWidget(win_desc)
        
        self.win_install_btn = QPushButton("Install Windows Layer")
        self.win_install_btn.setObjectName("primary")
        self.win_install_btn.clicked.connect(self._install_wine)
        win_layout.addWidget(self.win_install_btn)
        
        features_layout.addWidget(win_frame)
        features_layout.addStretch()
        
        self.tabs.addTab(self.features_tab, "Optional Features")
        
        layout.addWidget(self.tabs)
        
        # Load initial data if supported
        if self.pkg_mgr.is_supported():
            QTimer.singleShot(100, self._load_installed)
            
    def _load_installed(self):
        self.installed_table.setRowCount(0)
        packages = self.pkg_mgr.get_installed_packages()
        
        # Limit to 500 for performance in UI
        limit = min(len(packages), 500)
        self.installed_table.setRowCount(limit)
        
        for i in range(limit):
            pkg = packages[i]
            self.installed_table.setItem(i, 0, QTableWidgetItem(pkg.get("name", "")))
            self.installed_table.setItem(i, 1, QTableWidgetItem(pkg.get("version", "")))
            self.installed_table.setItem(i, 2, QTableWidgetItem(pkg.get("description", "")))
            
    def _check_updates(self):
        self.updates_table.setRowCount(0)
        packages = self.pkg_mgr.get_upgradable_packages()
        
        self.updates_table.setRowCount(len(packages))
        for i, pkg in enumerate(packages):
            self.updates_table.setItem(i, 0, QTableWidgetItem(pkg.get("name", "")))
            self.updates_table.setItem(i, 1, QTableWidgetItem(pkg.get("details", "")))
            
    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
            
        if not self.pkg_mgr.is_supported():
            QMessageBox.warning(self, "Not Supported", "Package management is not supported on this operating system.")
            return
            
        # Switch to installed tab and filter
        self.tabs.setCurrentWidget(self.installed_tab)
        
        # Simple local filter instead of apt-cache search for speed
        for i in range(self.installed_table.rowCount()):
            item = self.installed_table.item(i, 0)
            if item and query.lower() in item.text().lower():
                self.installed_table.setRowHidden(i, False)
            else:
                self.installed_table.setRowHidden(i, True)

    def _install_wine(self):
        """Attempts to install WineHQ for Windows diagnostic support."""
        if not self.pkg_mgr.is_supported():
            QMessageBox.critical(self, "NOT IMPLEMENTED", "Cannot install Wine: Package management (apt/dpkg) is not available on this host.")
            return
            
        # In a real scenario this would spawn a root subprocess for `apt-get install wine64`
        # Per core rules: do not fake success.
        QMessageBox.warning(
            self, 
            "Action Required", 
            "Installing the Windows Diagnostic Layer requires root privileges.\n\n"
            "Please open a terminal and run:\n"
            "sudo apt-get update && sudo apt-get install wine64 -y"
        )
