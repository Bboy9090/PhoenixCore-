#!/usr/bin/env python3
"""
Bobby's PhoenixDrive - Enhanced Desktop Application
Dual GUI/CLI support with modern theme and professional error handling
Integrated from PhoenixCore- BootForge implementation
"""

import sys
import os
import logging
import traceback
import argparse
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def _excepthook(exc_type, exc_value, exc_tb):
    """Centralized unhandled exception handler - logs before default behavior."""
    try:
        log = logging.getLogger("phoenixdrive.main")
        if log.handlers:
            log.critical(
                "Unhandled exception: %s",
                "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
            )
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)


sys.excepthook = _excepthook


def setup_logging(level=logging.INFO):
    """Setup logging configuration."""
    log_dir = Path.home() / ".phoenixdrive" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "phoenixdrive.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    
    return logging.getLogger(__name__)


def run_gui_mode():
    """Run application in GUI mode."""
    try:
        from src.ui.main_window import PhoenixDriveMainWindow
        from src.core.config import Config
        from src.ui.modern_theme import PhoenixDriveTheme
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        
        logger = logging.getLogger(__name__)
        logger.info("Starting PhoenixDrive GUI application...")
        
        # Enable high DPI scaling
        try:
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except (AttributeError, Exception):
            pass
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("PhoenixDrive")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("PhoenixDrive")
        
        # Apply modern theme
        PhoenixDriveTheme.apply_theme(app)
        
        # Initialize configuration
        config = Config()
        
        # Create main window
        main_window = PhoenixDriveMainWindow()
        main_window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except (ImportError, RuntimeError, Exception) as e:
        error_type = type(e).__name__
        logger = logging.getLogger(__name__)
        logger.error(f"GUI mode failed: {error_type}: {e}")
        
        print("\n🖥️  GUI Mode Not Available")
        print("═" * 50)
        print(f"Error Type: {error_type}")
        print(f"Reason: {e}")
        print("\n📋 Falling back to CLI mode...")
        print("💡 Note: GUI requires a desktop environment with Qt/OpenGL support")
        print("\n🚀 CLI mode provides full functionality!")
        print("   Use 'phoenixdrive --help' for available commands")
        print()
        
        return False


def run_cli_mode(args):
    """Run application in CLI mode."""
    try:
        from src.cli.cli_interface import create_cli_parser, execute_command
        
        logger = logging.getLogger(__name__)
        logger.info("Starting PhoenixDrive CLI application...")
        
        # Create CLI parser
        parser = create_cli_parser()
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Execute command
        return execute_command(parsed_args)
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"CLI mode failed: {e}", exc_info=True)
        print(f"Error: {e}")
        return False


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="phoenixdrive",
        description="Bobby's PhoenixDrive - Universal OS Deployment Tool",
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Force GUI mode (default if no command specified)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force CLI mode",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PhoenixDrive 2.0.0",
    )
    
    # Parse known args to check for mode
    args, remaining = parser.parse_known_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Determine mode
    gui_mode = args.gui or (not args.cli and len(remaining) == 0)
    
    # Auto-enable GUI on Windows if double-clicked
    if sys.platform.startswith("win") and len(sys.argv) == 1:
        gui_mode = True
    
    # Run appropriate mode
    if gui_mode:
        logger.info("Running in GUI mode")
        success = run_gui_mode()
        if not success:
            # Fallback to CLI
            logger.info("Falling back to CLI mode")
            run_cli_mode(remaining)
    else:
        logger.info("Running in CLI mode")
        run_cli_mode(sys.argv[1:])


if __name__ == "__main__":
    main()
