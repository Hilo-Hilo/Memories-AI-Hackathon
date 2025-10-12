"""
Logging configuration for Focus Guardian.

Provides structured logging to both console and file with appropriate
formatting and log levels for different modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str = "focus_guardian",
    log_dir: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Setup logger with console and file handlers.
    
    Args:
        name: Logger name
        log_dir: Directory for log files (if None, only console logging)
        console_level: Logging level for console output
        file_level: Logging level for file output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"focus_guardian_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

