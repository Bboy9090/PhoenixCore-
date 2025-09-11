#!/usr/bin/env python3
"""
BootForge - Professional Cross-Platform OS Deployment Tool
Main application entry point
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.main_window import BootForgeMainWindow
from src.core.config import Config
from src.core.logger import setup_logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    """Main application entry point"""
    # Enable high DPI scaling
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # Handle older PyQt6 versions
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("BootForge")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BootForge")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting BootForge application...")
    
    # Initialize configuration
    config = Config()
    
    # Create main window
    main_window = BootForgeMainWindow()
    main_window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()