import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from arcwyre.modules.control_center import ControlCenterModule
from arcwyre.modules.health import HealthModule
from arcwyre.modules.inspector import InspectorModule
from arcwyre.modules.bootforge import BootForgeModule
from arcwyre.modules.recovery import RecoveryModule
from arcwyre.modules.software import SoftwareModule
from arcwyre.modules.maintenance import MaintenanceModule
from arcwyre.modules.companion import CompanionModule

class ArcwyreControlCenter(QMainWindow):
    """Arcwyre Control Center Main Window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle("Arcwyre Control Center")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter for sidebar and content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        main_layout.addWidget(self.splitter)
        
        # Sidebar container
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 30, 10, 10)
        sidebar_layout.setSpacing(20)
        sidebar_container.setObjectName("sidebar")
        sidebar_container.setFixedWidth(280)
        
        # Logo header
        import os
        from PyQt6.QtGui import QPixmap
        logo_layout = QHBoxLayout()
        logo_icon = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "icons", "arcwyre-logo.svg")
        if os.path.exists(logo_path):
            logo_pix = QPixmap(logo_path)
            # Scale it down slightly
            logo_icon.setPixmap(logo_pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        logo_text = QLabel("ARCWYRE")
        logo_text.setStyleSheet("color: #F5F5F7; font-size: 18px; font-weight: 800; letter-spacing: 2px;")
        
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        sidebar_layout.addLayout(logo_layout)
        
        # Sidebar list
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar_list")
        self.sidebar.setIconSize(QSize(20, 20)) # Sleeker icons
        sidebar_layout.addWidget(self.sidebar)
        
        self.splitter.addWidget(sidebar_container)
        
        # Content Stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_area")
        self.splitter.addWidget(self.content_stack)
        
        # Set proportions
        self.splitter.setSizes([250, 950])
        self.splitter.setCollapsible(0, False)
        
        # Add modules
        self._init_modules()
        
        # Connect sidebar
        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        # Select first item
        if self.sidebar.count() > 0:
            self.sidebar.setCurrentRow(0)
            
    def _init_modules(self):
        """Initialize the 7 flagship applications"""
        import os
        icon_dir = os.path.join(os.path.dirname(__file__), "icons")
        
        modules = [
            ("Arcwyre Hub", "home.svg", ControlCenterModule()),
            ("System Health", "activity.svg", HealthModule()),
            ("Device Inspector", "search.svg", InspectorModule()),
            ("BootForge", "zap.svg", BootForgeModule()),
            ("Recovery Center", "life-buoy.svg", RecoveryModule()),
            ("Software Center", "package.svg", SoftwareModule()),
            ("Maintenance Hub", "settings.svg", MaintenanceModule()),
            ("Mobile Companion", "smartphone.svg", CompanionModule())
        ]
        
        for name, icon_file, widget in modules:
            # Add to sidebar
            icon_path = os.path.join(icon_dir, icon_file)
            item = QListWidgetItem(f" {name}")
            if os.path.exists(icon_path):
                # Set icon color via QSS or use plain SVGs
                item.setIcon(QIcon(icon_path))
            font = QFont()
            font.setPointSize(14)
            font.setBold(False)
            item.setFont(font)
            self.sidebar.addItem(item)
            
            # Add to stack
            self.content_stack.addWidget(widget)
