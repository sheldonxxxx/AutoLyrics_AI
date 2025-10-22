#!/usr/bin/env python3
"""
Centralized logging configuration for the Music Lyrics Processing Pipeline.

This module provides consistent logging setup with colored output and file logging
capabilities across all pipeline modules.
For comprehensive documentation, see: docs/modules/logging_config.md

Key Features:
- Colored console output with ANSI color codes
- File logging with persistent storage
- Hierarchical logger configuration
- Terminal compatibility and smart color detection
- Flexible log level and format configuration

Dependencies:
- logging (Python standard library)
- sys (system interface)
- pathlib (modern path handling)
- os (operating system interface)

Logger Colors: DEBUG(Cyan), INFO(Green), WARNING(Yellow), ERROR(Red), CRITICAL(Magenta)

Used By: All pipeline modules for consistent logging
"""
import os
import sys
import logging
import logfire

class ColoredFormatter(logging.Formatter):
    """A custom formatter that adds colors to log messages based on log level."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset to default
    }

    def format(self, record):
        # Add color to the level name
        if record.levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            # Create a copy of the record to avoid modifying the original
            record = logging.LogRecord(
                record.name, record.levelno, record.pathname, record.lineno,
                record.msg, record.args, record.exc_info
            )
            record.levelname = colored_levelname

        return super().format(record)


def setup_logging(level=logging.INFO, log_file=None, log_format=None, clear_handlers=True, use_colors=True, enable_logfire=False):
    """
    Set up consistent logging configuration for all scripts.

    Args:
        level: Logging level (default: logging.INFO)
        log_file: Optional file path to log to a file
        log_format: Custom log format string
        clear_handlers: Whether to clear existing handlers (default: True)
        use_colors: Whether to use colored output for console (default: True)
        enable_logfire: Whether to enable Logfire observability (default: False)
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

    # Configure Logfire if enabled
    if enable_logfire:
        try:
            logfire.configure(
                # environment=os.getenv('LOGFIRE_ENVIRONMENT', 'development'),
                token=os.getenv('LOGFIRE_WRITE_TOKEN'),
                console=False  # Disable console output from Logfire
            )
            logfire.instrument_pydantic_ai()
            # logfire.instrument_httpx(capture_all=True) 
            
            # Create handler that only sends to Logfire service
            logfire_handler = logfire.LogfireLoggingHandler()
            logger.addHandler(logfire_handler)
        except Exception as e:
            # Log the error but don't fail the entire setup
            print(f"Warning: Failed to configure Logfire: {e}", file=sys.stderr)

    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)

    # Use colored formatter for console if requested and supported
    if use_colors:
        try:
            # Test if terminal supports colors (basic check)
            import shutil
            if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
                # Use colored formatter for console
                colored_formatter = ColoredFormatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
                console_handler.setFormatter(colored_formatter)
            else:
                console_handler.setFormatter(formatter)
        except Exception:
            # Fall back to regular formatter if color setup fails
            console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(formatter)

    # Add console handler for consistent formatting
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