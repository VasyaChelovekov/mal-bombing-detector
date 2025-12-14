"""
Logging utilities for MAL Bombing Detector.

Provides centralized logging configuration with:
- File and console handlers
- Configurable log levels
- Colored console output
- Log rotation
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import get_config, ROOT_DIR


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for console output.
    
    Uses ANSI escape codes for coloring based on log level.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "mal_analyzer",
    log_level: Optional[str] = None,
    log_to_file: bool = True,
    colored: bool = True,
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        name: Logger name.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, uses config value.
        log_to_file: Whether to log to file.
        colored: Whether to use colored console output.
    
    Returns:
        Configured logger instance.
    """
    config = get_config()
    
    # Determine log level
    level_str = log_level or config.log_level
    level = getattr(logging, level_str.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if colored and config.cli.colored_output:
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_dir = config.logging.path
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate log filename
        date_str = datetime.now().strftime("%Y%m%d")
        log_filename = config.logging.filename_pattern.replace("{date}", date_str)
        log_path = log_dir / log_filename
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.logging.max_file_size_mb * 1024 * 1024,
            backupCount=config.logging.backup_count,
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        
        file_formatter = logging.Formatter(
            config.logging.format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "mal_analyzer") -> logging.Logger:
    """
    Get or create a logger.
    
    Args:
        name: Logger name.
    
    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    
    # If no handlers, set up logging
    if not logger.handlers:
        return setup_logging(name)
    
    return logger
