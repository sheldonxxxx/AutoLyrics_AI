#!/usr/bin/env python3
"""
Configuration module for consistent logging across all scripts.
"""

import logging
import sys
from pathlib import Path
import os


def setup_logging(level=logging.INFO, log_file=None, log_format=None, clear_handlers=True):
    """
    Set up consistent logging configuration for all scripts.
    
    Args:
        level: Logging level (default: logging.INFO)
        log_file: Optional file path to log to a file
        log_format: Custom log format string
        clear_handlers: Whether to clear existing handlers (default: True)
    """
    # Default log format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    formatter = logging.Formatter(
        log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers if requested
    if clear_handlers:
        logger.handlers.clear()
    
    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name, level=None):
    """
    Get a named logger instance with optional level setting.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        level: Optional logging level to set for this logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger