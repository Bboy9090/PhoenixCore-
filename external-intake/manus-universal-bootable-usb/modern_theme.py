"""
PhoenixDrive Modern Theme System
Professional PyQt6 styling with dark/light mode support
"""

from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class PhoenixDriveTheme:
    """Modern theme for PhoenixDrive application."""
    
    # Color palette
    PRIMARY_COLOR = "#FF6B35"  # Orange
    SECONDARY_COLOR = "#004E89"  # Dark Blue
    SUCCESS_COLOR = "#06A77D"  # Green
    WARNING_COLOR = "#F77F00"  # Orange
    ERROR_COLOR = "#D62828"  # Red
    
    BACKGROUND_DARK = "#1A1A1A"
    BACKGROUND_LIGHT = "#F5F5F5"
    SURFACE_DARK = "#2D2D2D"
    SURFACE_LIGHT = "#FFFFFF"
    TEXT_DARK = "#FFFFFF"
    TEXT_LIGHT = "#1A1A1A"
    BORDER_COLOR = "#404040"
    
    @classmethod
    def apply_theme(cls, app: QApplication, dark_mode: bool = True):
        """Apply theme to application."""
        if dark_mode:
            cls._apply_dark_theme(app)
        else:
            cls._apply_light_theme(app)
    
    @classmethod
    def _apply_dark_theme(cls, app: QApplication):
        """Apply dark theme."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.BACKGROUND_DARK))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.SURFACE_DARK))
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.TEXT_DARK))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#808080"))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.SURFACE_DARK))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.TEXT_DARK))
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.TEXT_DARK))
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(cls.SECONDARY_COLOR))
        
        app.setPalette(palette)
        
        # Apply stylesheet
        stylesheet = cls._get_dark_stylesheet()
        app.setStyle("Fusion")
        app.setStyleSheet(stylesheet)
    
    @classmethod
    def _apply_light_theme(cls, app: QApplication):
        """Apply light theme."""
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.BACKGROUND_LIGHT))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.SURFACE_LIGHT))
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.TEXT_LIGHT))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#808080"))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.SURFACE_LIGHT))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.TEXT_LIGHT))
        
        # Highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.TEXT_DARK))
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.PRIMARY_COLOR))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(cls.SECONDARY_COLOR))
        
        app.setPalette(palette)
        
        # Apply stylesheet
        stylesheet = cls._get_light_stylesheet()
        app.setStyle("Fusion")
        app.setStyleSheet(stylesheet)
    
    @classmethod
    def _get_dark_stylesheet(cls) -> str:
        """Get dark theme stylesheet."""
        return f"""
        QMainWindow {{
            background-color: {cls.BACKGROUND_DARK};
            color: {cls.TEXT_DARK};
        }}
        
        QWidget {{
            background-color: {cls.BACKGROUND_DARK};
            color: {cls.TEXT_DARK};
        }}
        
        QPushButton {{
            background-color: {cls.PRIMARY_COLOR};
            color: {cls.TEXT_DARK};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: #FF8C5A;
        }}
        
        QPushButton:pressed {{
            background-color: #E55A24;
        }}
        
        QPushButton:disabled {{
            background-color: #404040;
            color: #808080;
        }}
        
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {cls.SURFACE_DARK};
            color: {cls.TEXT_DARK};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {cls.PRIMARY_COLOR};
        }}
        
        QLabel {{
            color: {cls.TEXT_DARK};
        }}
        
        QTabBar::tab {{
            background-color: {cls.SURFACE_DARK};
            color: {cls.TEXT_DARK};
            padding: 8px 20px;
            border: 1px solid {cls.BORDER_COLOR};
        }}
        
        QTabBar::tab:selected {{
            background-color: {cls.PRIMARY_COLOR};
            color: {cls.TEXT_DARK};
        }}
        
        QProgressBar {{
            background-color: {cls.SURFACE_DARK};
            border: 1px solid {cls.BORDER_COLOR};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        
        QMenuBar {{
            background-color: {cls.SURFACE_DARK};
            color: {cls.TEXT_DARK};
            border-bottom: 1px solid {cls.BORDER_COLOR};
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        
        QMenu {{
            background-color: {cls.SURFACE_DARK};
            color: {cls.TEXT_DARK};
            border: 1px solid {cls.BORDER_COLOR};
        }}
        
        QMenu::item:selected {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        """
    
    @classmethod
    def _get_light_stylesheet(cls) -> str:
        """Get light theme stylesheet."""
        return f"""
        QMainWindow {{
            background-color: {cls.BACKGROUND_LIGHT};
            color: {cls.TEXT_LIGHT};
        }}
        
        QWidget {{
            background-color: {cls.BACKGROUND_LIGHT};
            color: {cls.TEXT_LIGHT};
        }}
        
        QPushButton {{
            background-color: {cls.PRIMARY_COLOR};
            color: {cls.TEXT_DARK};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: #FF8C5A;
        }}
        
        QPushButton:pressed {{
            background-color: #E55A24;
        }}
        
        QPushButton:disabled {{
            background-color: #E0E0E0;
            color: #808080;
        }}
        
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {cls.SURFACE_LIGHT};
            color: {cls.TEXT_LIGHT};
            border: 1px solid #D0D0D0;
            border-radius: 4px;
            padding: 6px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {cls.PRIMARY_COLOR};
        }}
        
        QLabel {{
            color: {cls.TEXT_LIGHT};
        }}
        
        QTabBar::tab {{
            background-color: #E8E8E8;
            color: {cls.TEXT_LIGHT};
            padding: 8px 20px;
            border: 1px solid #D0D0D0;
        }}
        
        QTabBar::tab:selected {{
            background-color: {cls.PRIMARY_COLOR};
            color: {cls.TEXT_DARK};
        }}
        
        QProgressBar {{
            background-color: {cls.SURFACE_LIGHT};
            border: 1px solid #D0D0D0;
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        
        QMenuBar {{
            background-color: #F0F0F0;
            color: {cls.TEXT_LIGHT};
            border-bottom: 1px solid #D0D0D0;
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        
        QMenu {{
            background-color: {cls.SURFACE_LIGHT};
            color: {cls.TEXT_LIGHT};
            border: 1px solid #D0D0D0;
        }}
        
        QMenu::item:selected {{
            background-color: {cls.PRIMARY_COLOR};
        }}
        """
