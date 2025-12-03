"""
Logging configuration for Necro Game News.

Provides consistent logging setup across all modules.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

# Get log level from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/necro_news.log')


def setup_logging(name: str = None, level: str = None):
    """
    Set up logging with file and console handlers.
    
    Args:
        name: Logger name (uses __name__ if not provided)
        level: Log level (uses env var if not provided)
    """
    if level is None:
        level = LOG_LEVEL
    
    # Ensure logs directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - all logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Return logger for specific module if name provided
    if name:
        return logging.getLogger(name)
    
    return root_logger


def get_logger(name: str):
    """
    Get a logger for a specific module.
    
    Args:
        name: Module name (typically __name__)
    """
    return logging.getLogger(name)
