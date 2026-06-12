#!/usr/bin/env python3
"""
Arcwyre OS Control Center
Flagship application suite hub
"""

import sys
import os
from pathlib import Path
import logging

# Add the existing desktop folder to Python path to reuse core services
project_root = Path(__file__).resolve().parent.parent.parent
desktop_path = project_root / "desktop"
sys.path.insert(0, str(desktop_path))

# Add arcwyre path
arcwyre_path = Path(__file__).resolve().parent
sys.path.insert(0, str(arcwyre_path))

def main():
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        # High DPI scaling
        if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            
        app = QApplication(sys.argv)
        app.setApplicationName("Arcwyre Control Center")
        app.setApplicationVersion("1.0.0")
        
        # Load user-friendly Inter font
        from PyQt6.QtGui import QFontDatabase, QFont
        font_path = os.path.join(arcwyre_path, "arcwyre", "Inter.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                app.setFont(QFont(font_family))
        
        # Apply ultra-premium Arcwyre theme
        from arcwyre.theme import get_stylesheet
        app.setStyleSheet(get_stylesheet())
        
        from arcwyre.app import ArcwyreControlCenter
        
        window = ArcwyreControlCenter()
        window.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error starting Arcwyre Control Center: {e}")
        print("Please ensure PyQt6 is installed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
