"""
Logging Utility - Setup and manage application logging
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(app_name: str, log_level=logging.INFO) -> logging.Logger:
    """
    Setup application logging
    
    Args:
        app_name: Application name for logger
        log_level: Logging level (default: INFO)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(log_level)
    
    # Create logs directory
    log_dir = Path.home() / '.phoenixdrive' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    log_file = log_dir / f'{app_name}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger
