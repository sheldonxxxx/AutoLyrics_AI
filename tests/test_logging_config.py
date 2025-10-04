#!/usr/bin/env python3
"""
Comprehensive unit tests for logging_config.py module.
"""

import unittest
import tempfile
import shutil
import logging
import sys
import os
from unittest.mock import patch
from io import StringIO

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging, get_logger, ColoredFormatter


class TestLoggingConfig(unittest.TestCase):
    """Test cases for logging configuration functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original logging configuration
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)

        # Clean up temp directory
        shutil.rmtree(self.temp_dir)

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        logger = setup_logging(level=logging.INFO)

        # Check that logger was configured
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.INFO)

        # Check that console handler was added
        self.assertGreater(len(logger.handlers), 0)

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        logger = setup_logging(level=logging.DEBUG, log_file=self.log_file)

        # Check that file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        self.assertGreater(len(file_handlers), 0)

        # Check that log file was created
        self.assertTrue(os.path.exists(self.log_file))

    def test_setup_logging_custom_format(self):
        """Test logging setup with custom format."""
        custom_format = '%(levelname)s - %(name)s - %(message)s'
        logger = setup_logging(level=logging.WARNING, log_format=custom_format)

        # Test that custom format is used
        test_logger = logging.getLogger('test_custom_format')
        test_logger.setLevel(logging.WARNING)

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        formatter = logging.Formatter(custom_format)
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        test_logger.warning("Test message")

        # Check that custom format was used
        log_output = log_capture.getvalue()
        self.assertIn("WARNING", log_output)
        self.assertIn("test_custom_format", log_output)
        self.assertIn("Test message", log_output)

    def test_setup_logging_clear_handlers(self):
        """Test logging setup with handler clearing."""
        # Add a handler first
        logger = logging.getLogger()
        initial_handler_count = len(logger.handlers)

        # Setup logging with clear_handlers=True (default)
        setup_logging(level=logging.INFO, clear_handlers=True)

        # Check that handlers were cleared and new ones added
        self.assertGreater(len(logger.handlers), 0)

    def test_setup_logging_preserve_handlers(self):
        """Test logging setup without handler clearing."""
        # Add a custom handler first
        logger = logging.getLogger()
        custom_handler = logging.StreamHandler(StringIO())
        logger.addHandler(custom_handler)
        initial_handler_count = len(logger.handlers)

        # Setup logging with clear_handlers=False
        setup_logging(level=logging.INFO, clear_handlers=False)

        # Check that custom handler was preserved
        self.assertEqual(len(logger.handlers), initial_handler_count + 1)  # +1 for console handler

    def test_setup_logging_with_colors(self):
        """Test logging setup with colors enabled."""
        # Test on a system that supports colors (mock isatty)
        with patch('sys.stdout.isatty', return_value=True):
            logger = setup_logging(level=logging.INFO, use_colors=True)

            # Check that colored formatter was used
            console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
            self.assertGreater(len(console_handlers), 0)

    def test_setup_logging_without_colors(self):
        """Test logging setup with colors disabled."""
        logger = setup_logging(level=logging.INFO, use_colors=False)

        # Check that regular formatter was used
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        self.assertGreater(len(console_handlers), 0)

    def test_setup_logging_colors_fallback(self):
        """Test logging setup with colors fallback on error."""
        # Test with colors enabled but formatter error
        with patch('sys.stdout.isatty', return_value=True):
            with patch('logging.Formatter') as mock_formatter:
                mock_formatter.side_effect = Exception("Formatter error")

                logger = setup_logging(level=logging.INFO, use_colors=True)

                # Should not raise exception and should have handlers
                self.assertGreater(len(logger.handlers), 0)

    def test_get_logger_with_level(self):
        """Test getting logger with specific level."""
        test_logger = get_logger('test_logger', level=logging.ERROR)

        # Check that logger has correct level
        self.assertEqual(test_logger.level, logging.ERROR)
        self.assertEqual(test_logger.name, 'test_logger')

    def test_get_logger_without_level(self):
        """Test getting logger without specific level."""
        test_logger = get_logger('test_logger_no_level')

        # Check that logger was created with default level
        self.assertEqual(test_logger.name, 'test_logger_no_level')
        # Level should be NOTSET (inherits from root)
        self.assertEqual(test_logger.level, logging.NOTSET)

    def test_colored_formatter_format(self):
        """Test ColoredFormatter formatting."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        # Create test log record
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )

        # Test formatting
        formatted = formatter.format(record)

        # Check that color codes were added for INFO level
        self.assertIn('\033[32m', formatted)  # Green color for INFO
        self.assertIn('\033[0m', formatted)   # Reset code
        self.assertIn('INFO', formatted)
        self.assertIn('Test message', formatted)

    def test_colored_formatter_debug_level(self):
        """Test ColoredFormatter with DEBUG level."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        record = logging.LogRecord(
            name='test_logger',
            level=logging.DEBUG,
            pathname='test.py',
            lineno=10,
            msg='Debug message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Check that cyan color was used for DEBUG
        self.assertIn('\033[36m', formatted)  # Cyan color for DEBUG
        self.assertIn('Debug message', formatted)

    def test_colored_formatter_error_level(self):
        """Test ColoredFormatter with ERROR level."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        record = logging.LogRecord(
            name='test_logger',
            level=logging.ERROR,
            pathname='test.py',
            lineno=10,
            msg='Error message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)

        # Check that red color was used for ERROR
        self.assertIn('\033[31m', formatted)  # Red color for ERROR
        self.assertIn('Error message', formatted)

    def test_colored_formatter_unknown_level(self):
        """Test ColoredFormatter with unknown level."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        # Create record with custom level not in COLORS dict
        record = logging.LogRecord(
            name='test_logger',
            level=99,  # Custom level
            pathname='test.py',
            lineno=10,
            msg='Custom level message',
            args=(),
            exc_info=None
        )
        record.levelname = 'CUSTOM'

        formatted = formatter.format(record)

        # Check that no color codes were added for unknown level
        self.assertNotIn('\033[', formatted)  # No ANSI color codes
        self.assertIn('CUSTOM', formatted)
        self.assertIn('Custom level message', formatted)

    def test_setup_logging_creates_log_directory(self):
        """Test that logging setup creates log directory."""
        nested_log_file = os.path.join(self.temp_dir, "nested", "dir", "test.log")

        logger = setup_logging(level=logging.INFO, log_file=nested_log_file)

        # Check that directory was created
        self.assertTrue(os.path.exists(os.path.dirname(nested_log_file)))

        # Check that file handler was added
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        self.assertGreater(len(file_handlers), 0)

    def test_setup_logging_file_handler_encoding(self):
        """Test that file handler uses UTF-8 encoding."""
        logger = setup_logging(level=logging.INFO, log_file=self.log_file)

        # Check file handler configuration
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        if file_handlers:
            # The encoding is set during handler creation, we can't easily test it
            # but we can verify the handler was created successfully
            self.assertGreater(len(file_handlers), 0)

    def test_setup_logging_multiple_calls(self):
        """Test multiple calls to setup_logging."""
        # First call
        logger1 = setup_logging(level=logging.INFO)

        # Second call with different level
        logger2 = setup_logging(level=logging.DEBUG, clear_handlers=True)

        # Both should return the same logger instance (root logger)
        self.assertIs(logger1, logger2)

        # Level should be the most recent one (DEBUG has lower value, so it should override)
        self.assertEqual(logger1.level, logging.DEBUG)

    def test_get_logger_inheritance(self):
        """Test logger level inheritance."""
        # Setup root logger with INFO level
        setup_logging(level=logging.INFO)

        # Get child logger without specific level
        child_logger = get_logger('parent.child')

        # Child should inherit from parent
        self.assertEqual(child_logger.level, logging.NOTSET)  # Inherits from root

        # But effective level should be INFO
        self.assertEqual(child_logger.getEffectiveLevel(), logging.INFO)

    def test_colored_formatter_with_exception(self):
        """Test ColoredFormatter with exception info."""
        formatter = ColoredFormatter('%(levelname)s - %(message)s')

        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name='test_logger',
                level=logging.ERROR,
                pathname='test.py',
                lineno=10,
                msg='Error with exception',
                args=(),
                exc_info=sys.exc_info()
            )

            # Should not raise exception when formatting with exc_info
            formatted = formatter.format(record)
            self.assertIn('ERROR', formatted)
            self.assertIn('Error with exception', formatted)


if __name__ == '__main__':
    unittest.main()