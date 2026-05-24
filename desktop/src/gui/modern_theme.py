"""
BootForge Modern Theme System
Professional styling and color palette for the application
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication


class BootForgeTheme:
    """Professional theme configuration for BootForge"""
    
    # Color Palette - Premium Blue Phoenix & Home Aurelia Gold Theme
    COLORS = {
        # Primary colors - Vibrant Electric Blue gradient
        "primary": "#00d2ff",           # Electric blue
        "primary_hover": "#00b0ff",     # Deeper electric blue on hover
        "primary_pressed": "#0088cc",   # Darker blue on press
        "primary_gradient": "linear-gradient(135deg, #00d2ff 0%, #0088cc 100%)",
        
        # Background colors - Deep Space Navy base
        "bg_primary": "#050811",        # Extreme deep navy space background
        "bg_secondary": "#0a0e1a",      # Deep navy panels
        "bg_tertiary": "#111827",       # Elevated slate navy
        "bg_input": "#0d1527",          # Deep navy input backgrounds
        "bg_card": "#080c16",           # Card backgrounds
        
        # Surface colors - Dark metallic space elements
        "surface": "#070b14",           # Menu bars, toolbars
        "surface_hover": "#1a233a",     # Hover state with electric blue tint
        "surface_pressed": "#101625",   # Pressed state with dark blue tint
        
        # Border colors - Gold and Electric Blue accent systems
        "border": "#1e293b",            # Subtle borders
        "border_light": "#334155",      # Lighter borders
        "border_focus": "#00d2ff",      # Electric blue focused borders
        "border_accent": "#ffd700",     # Premium Gold Trim accents
        
        # Text colors - High contrast whites & Slates
        "text_primary": "#ffffff",      # Pure white primary text
        "text_secondary": "#cbd5e1",    # Light slate secondary text
        "text_muted": "#94a3b8",        # Muted text
        "text_disabled": "#475569",     # Disabled text
        "text_orange": "#ffd700",       # Gold text accents (maintains stylesheet compatibility)
        
        # Status colors - Styled to match electric theme
        "success": "#10b981",           # Emerald green success
        "warning": "#ffd700",           # Gold warning
        "error": "#f43f5e",             # Crimson error
        "info": "#00d2ff",              # Electric blue info
        
        # Accent colors - Gold Trim, Arcwyre Purple, and Thunder God Neon Cyan
        "accent": "#ffd700",            # Default accent color (Premium Gold)
        "accent_1": "#9d4edd",          # Arcwyre Purple accent
        "accent_2": "#00ffff",          # Thunder God Neon Cyan accent
        "accent_3": "#ffd700",          # Gold Trim
        "accent_gradient_1": "linear-gradient(135deg, #00d2ff 0%, #9d4edd 100%)", # Electric Blue to Purple
        "accent_gradient_2": "linear-gradient(90deg, #00ffff 0%, #00d2ff 100%)",  # Neon Cyan to Blue
    }
    
    # Typography
    FONTS = {
        "default_family": "Segoe UI, system-ui, sans-serif",
        "monospace_family": "Consolas, 'Courier New', monospace",
        "sizes": {
            "xs": 10,
            "sm": 12,
            "base": 14,
            "lg": 16,
            "xl": 18,
            "2xl": 24,
            "3xl": 30,
        }
    }
    
    # Spacing
    SPACING = {
        "xs": 4,
        "sm": 8,
        "base": 16,
        "lg": 24,
        "xl": 32,
        "2xl": 48,
        "3xl": 64,
    }
    
    # Border radius
    RADIUS = {
        "sm": 4,
        "base": 6,
        "lg": 8,
        "xl": 12,
        "full": 9999,
    }
    
    # Enhanced Shadows - Modern with electric blue & gold glows
    SHADOWS = {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.4)",
        "base": "0 2px 4px 0 rgba(0, 0, 0, 0.5), 0 1px 2px 0 rgba(0, 0, 0, 0.3)",
        "lg": "0 4px 8px -1px rgba(0, 0, 0, 0.6), 0 2px 4px -1px rgba(0, 0, 0, 0.4)",
        "xl": "0 10px 20px -3px rgba(0, 0, 0, 0.7), 0 4px 8px -2px rgba(0, 0, 0, 0.5)",
        "orange_glow": "0 0 12px rgba(0, 210, 255, 0.4), 0 0 25px rgba(0, 210, 255, 0.15)", # Electric blue glow
        "purple_glow": "0 0 10px rgba(157, 78, 221, 0.5)",
        "inset": "inset 0 2px 4px 0 rgba(0, 0, 0, 0.5)",
    }
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """Get the complete application stylesheet"""
        return f"""
        /* === MAIN APPLICATION === */
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['bg_primary']}, stop:1 {cls.COLORS['bg_secondary']});
            color: {cls.COLORS['text_primary']};
            font-family: {cls.FONTS['default_family']};
            font-size: {cls.FONTS['sizes']['base']}px;
        }}
        
        /* === MENU BAR === */
        QMenuBar {{
            background-color: {cls.COLORS['surface']};
            color: {cls.COLORS['text_primary']};
            border-bottom: 1px solid {cls.COLORS['border']};
            padding: 4px 0px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 12px;
            border-radius: {cls.RADIUS['sm']}px;
            margin: 2px 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.COLORS['surface_hover']};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {cls.COLORS['surface_pressed']};
        }}
        
        QMenu {{
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['base']}px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: {cls.RADIUS['sm']}px;
            margin: 1px;
        }}
        
        QMenu::item:selected {{
            background-color: {cls.COLORS['primary']};
        }}
        
        /* === TOOLBAR === */
        QToolBar {{
            background-color: {cls.COLORS['surface']};
            border: none;
            spacing: {cls.SPACING['sm']}px;
            padding: {cls.SPACING['sm']}px;
        }}
        
        QToolBar::separator {{
            background-color: {cls.COLORS['border']};
            width: 1px;
            margin: 4px 8px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: {cls.RADIUS['base']}px;
            padding: 8px 12px;
            color: {cls.COLORS['text_primary']};
            font-weight: 500;
        }}
        
        QToolButton:hover {{
            background-color: {cls.COLORS['surface_hover']};
        }}
        
        QToolButton:pressed {{
            background-color: {cls.COLORS['surface_pressed']};
        }}
        
        /* === STATUS BAR === */
        QStatusBar {{
            background-color: {cls.COLORS['surface']};
            border-top: 1px solid {cls.COLORS['border']};
            color: {cls.COLORS['text_secondary']};
            padding: 4px 8px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* === TABS === */
        QTabWidget::pane {{
            border: 2px solid {cls.COLORS['border']};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_card']}, stop:1 {cls.COLORS['bg_secondary']});
            border-radius: {cls.RADIUS['lg']}px;
            margin-top: 4px;
        }}
        
        QTabBar::tab {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_tertiary']}, stop:1 {cls.COLORS['bg_secondary']});
            color: {cls.COLORS['text_secondary']};
            padding: 14px 24px;
            margin-right: 3px;
            border-top-left-radius: {cls.RADIUS['lg']}px;
            border-top-right-radius: {cls.RADIUS['lg']}px;
            font-weight: 600;
            border: 2px solid {cls.COLORS['border']};
            border-bottom: none;
        }}
        
        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['primary_hover']});
            color: {cls.COLORS['text_primary']};
            border: 3px solid {cls.COLORS['border_focus']};
            border-bottom: none;
        }}
        
        QTabBar::tab:hover:!selected {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['surface_hover']}, stop:1 {cls.COLORS['bg_tertiary']});
            color: {cls.COLORS['text_orange']};
            border-color: {cls.COLORS['border_accent']};
        }}
        
        /* === BUTTONS === */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_tertiary']}, stop:1 {cls.COLORS['bg_secondary']});
            border: 2px solid {cls.COLORS['border']};
            padding: 12px 24px;
            border-radius: {cls.RADIUS['lg']}px;
            color: {cls.COLORS['text_primary']};
            font-weight: 600;
            min-height: 24px;
            font-size: {cls.FONTS['sizes']['base']}px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['surface_hover']}, stop:1 {cls.COLORS['bg_tertiary']});
            border: 2px solid {cls.COLORS['border_accent']};
            color: {cls.COLORS['text_orange']};
        }}
        
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['surface_pressed']}, stop:1 {cls.COLORS['bg_secondary']});
            border: 2px solid {cls.COLORS['primary']};
        }}
        
        QPushButton:disabled {{
            background-color: {cls.COLORS['bg_input']};
            color: {cls.COLORS['text_disabled']};
            border-color: {cls.COLORS['border']};
        }}
        
        /* Primary button style */
        QPushButton[class="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['primary_hover']});
            border: 3px solid {cls.COLORS['border_focus']};
            color: {cls.COLORS['text_primary']};
            font-weight: 700;
        }}
        
        QPushButton[class="primary"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['accent_3']}, stop:1 {cls.COLORS['primary']});
            border: 3px solid {cls.COLORS['accent_3']};
        }}
        
        QPushButton[class="primary"]:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['primary_pressed']}, stop:1 {cls.COLORS['primary_hover']});
            border: 2px solid {cls.COLORS['primary_pressed']};
        }}
        
        /* === GROUP BOXES === */
        QGroupBox {{
            font-weight: 700;
            border: 2px solid {cls.COLORS['border_accent']};
            border-radius: {cls.RADIUS['xl']}px;
            margin-top: 20px;
            color: {cls.COLORS['text_primary']};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_card']}, stop:1 {cls.COLORS['bg_secondary']});
            padding-top: 16px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 20px;
            padding: 4px 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['accent_3']});
            color: {cls.COLORS['text_primary']};
            border: 2px solid {cls.COLORS['accent_3']};
            border-radius: {cls.RADIUS['base']}px;
            font-weight: 700;
        }}
        
        /* === PROGRESS BARS === */
        QProgressBar {{
            border: 2px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['lg']}px;
            text-align: center;
            color: {cls.COLORS['text_primary']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['bg_input']}, stop:1 {cls.COLORS['bg_tertiary']});
            font-weight: 600;
            min-height: 24px;
            max-height: 24px;
            font-size: {cls.FONTS['sizes']['sm']}px;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['primary']}, stop:0.5 {cls.COLORS['accent_3']}, stop:1 {cls.COLORS['primary_hover']});
            border-radius: {cls.RADIUS['base']}px;
            border: 1px solid {cls.COLORS['accent_3']};
            margin: 2px;
        }}
        
        /* === LABELS === */
        QLabel {{
            color: {cls.COLORS['text_primary']};
            background-color: transparent;
        }}
        
        QLabel[class="secondary"] {{
            color: {cls.COLORS['text_secondary']};
        }}
        
        QLabel[class="muted"] {{
            color: {cls.COLORS['text_muted']};
        }}
        
        QLabel[class="heading"] {{
            font-size: {cls.FONTS['sizes']['2xl']}px;
            font-weight: 700;
            color: {cls.COLORS['text_primary']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['text_primary']}, stop:0.7 {cls.COLORS['text_orange']}, stop:1 {cls.COLORS['accent_1']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        QLabel[class="subheading"] {{
            font-size: {cls.FONTS['sizes']['xl']}px;
            font-weight: 600;
            color: {cls.COLORS['text_orange']};
        }}
        
        QLabel[class="accent"] {{
            color: {cls.COLORS['text_orange']};
            font-weight: 600;
        }}
        
        QLabel[class="purple-accent"] {{
            color: {cls.COLORS['accent_1']};
            font-weight: 600;
        }}
        
        /* === INPUT FIELDS === */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_input']}, stop:1 {cls.COLORS['bg_secondary']});
            border: 2px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['lg']}px;
            padding: 10px 16px;
            color: {cls.COLORS['text_primary']};
            selection-background-color: {cls.COLORS['primary']};
            font-size: {cls.FONTS['sizes']['base']}px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 3px solid {cls.COLORS['border_focus']};
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_tertiary']}, stop:1 {cls.COLORS['bg_input']});
        }}
        
        /* === COMBO BOXES === */
        QComboBox {{
            background-color: {cls.COLORS['bg_input']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['base']}px;
            padding: 8px 12px;
            color: {cls.COLORS['text_primary']};
            min-width: 100px;
        }}
        
        QComboBox:hover {{
            border-color: {cls.COLORS['border_light']};
        }}
        
        QComboBox:focus {{
            border-color: {cls.COLORS['border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {cls.COLORS['text_secondary']};
            width: 0px;
            height: 0px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['base']}px;
            selection-background-color: {cls.COLORS['primary']};
        }}
        
        /* === LIST WIDGETS === */
        QListWidget {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_secondary']}, stop:1 {cls.COLORS['bg_primary']});
            border: 2px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['lg']}px;
            alternate-background-color: {cls.COLORS['bg_tertiary']};
        }}
        
        QListWidget::item {{
            padding: 12px 16px;
            border-bottom: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['sm']}px;
            margin: 1px;
        }}
        
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['accent_3']});
            color: {cls.COLORS['text_primary']};
            font-weight: 600;
            border: 2px solid {cls.COLORS['accent_3']};
        }}
        
        QListWidget::item:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['surface_hover']}, stop:1 {cls.COLORS['bg_tertiary']});
            color: {cls.COLORS['text_orange']};
        }}
        
        /* === TREE WIDGETS === */
        QTreeWidget {{
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['base']}px;
            alternate-background-color: {cls.COLORS['bg_tertiary']};
        }}
        
        QTreeWidget::item {{
            padding: 4px 8px;
            border-bottom: 1px solid {cls.COLORS['border']};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {cls.COLORS['primary']};
        }}
        
        QTreeWidget::item:hover {{
            background-color: {cls.COLORS['surface_hover']};
        }}
        
        /* === SCROLL BARS === */
        QScrollBar:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['bg_input']}, stop:1 {cls.COLORS['bg_secondary']});
            width: 14px;
            border-radius: 7px;
            border: 1px solid {cls.COLORS['border']};
        }}
        
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['border_light']}, stop:1 {cls.COLORS['text_muted']});
            border-radius: 6px;
            min-height: 30px;
            border: 1px solid {cls.COLORS['border']};
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cls.COLORS['accent_3']}, stop:1 {cls.COLORS['primary']});
            border: 2px solid {cls.COLORS['accent_3']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_input']}, stop:1 {cls.COLORS['bg_secondary']});
            height: 14px;
            border-radius: 7px;
            border: 1px solid {cls.COLORS['border']};
        }}
        
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['border_light']}, stop:1 {cls.COLORS['text_muted']});
            border-radius: 6px;
            min-width: 30px;
            border: 1px solid {cls.COLORS['border']};
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['accent_3']}, stop:1 {cls.COLORS['primary']});
            border: 2px solid {cls.COLORS['accent_3']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* === SPLITTERS === */
        QSplitter::handle {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['border']}, stop:1 {cls.COLORS['border_light']});
        }}
        
        QSplitter::handle:horizontal {{
            width: 3px;
        }}
        
        QSplitter::handle:vertical {{
            height: 3px;
        }}
        
        QSplitter::handle:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['accent_3']});
        }}
        
        /* === FRAMES === */
        QFrame {{
            background-color: transparent;
            border: none;
        }}
        
        QFrame[class="card"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {cls.COLORS['bg_card']}, stop:1 {cls.COLORS['bg_secondary']});
            border: 2px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['xl']}px;
            padding: {cls.SPACING['lg']}px;
        }}
        
        QFrame[class="elevated"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['bg_tertiary']}, stop:1 {cls.COLORS['bg_secondary']});
            border: 2px solid {cls.COLORS['border_light']};
            border-radius: {cls.RADIUS['xl']}px;
        }}
        
        QFrame[class="modern-card"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['bg_primary']}, stop:0.3 {cls.COLORS['bg_secondary']}, stop:1 {cls.COLORS['bg_tertiary']});
            border: 3px solid {cls.COLORS['border_accent']};
            border-radius: {cls.RADIUS['xl']}px;
            padding: {cls.SPACING['xl']}px;
        }}
        
        /* === CHECKBOXES === */
        QCheckBox {{
            color: {cls.COLORS['text_primary']};
            spacing: 12px;
            font-weight: 500;
        }}
        
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['sm']}px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['bg_input']}, stop:1 {cls.COLORS['bg_secondary']});
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {cls.COLORS['border_accent']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['bg_tertiary']}, stop:1 {cls.COLORS['bg_input']});
        }}
        
        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {cls.COLORS['primary']}, stop:1 {cls.COLORS['accent_3']});
            border: 2px solid {cls.COLORS['primary']};
        }}
        
        /* === TABLE WIDGETS === */
        QTableWidget {{
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {cls.COLORS['border']};
            border-radius: {cls.RADIUS['base']}px;
            gridline-color: {cls.COLORS['border']};
        }}
        
        QTableWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid {cls.COLORS['border']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {cls.COLORS['primary']};
        }}
        
        QHeaderView::section {{
            background-color: {cls.COLORS['bg_tertiary']};
            border: 1px solid {cls.COLORS['border']};
            padding: 8px 12px;
            font-weight: 600;
        }}
        """
    
    @classmethod
    def apply_theme(cls, app: QApplication):
        """Apply the theme to the application"""
        # Set global font
        font = QFont(cls.FONTS['default_family'])
        font.setPointSize(cls.FONTS['sizes']['base'])
        app.setFont(font)
        
        # Apply stylesheet
        app.setStyleSheet(cls.get_stylesheet())
        
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.COLORS['bg_primary']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.COLORS['bg_secondary']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.COLORS['bg_tertiary']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(cls.COLORS['bg_tertiary']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.COLORS['bg_tertiary']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(cls.COLORS['text_primary']))
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.COLORS['primary']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.COLORS['primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.COLORS['text_primary']))
        
        app.setPalette(palette)