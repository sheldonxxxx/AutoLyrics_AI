# Logging Configuration Module

## 📋 Centralized Logging System (`logging_config.py`)

Provides centralized logging configuration for the entire Music Lyrics Processing Pipeline. This module ensures consistent log formatting, colored output support, and flexible configuration across all pipeline modules. The logging system is essential for monitoring, debugging, and troubleshooting the complex multi-step processing workflow.

## Pipeline Integration

```
All Pipeline       ┌──────────────────┐    Console + Files
Modules     ◀────▶ │  logging_config  │ ◀────▶ (formatted output)
                    │  (centralized    │
                    │  logging)        │
                    └──────────────────┘
```

## Core Functionality

### Primary Features
1. **Colored Console Output**: Visual log level distinction with ANSI colors
2. **File Logging**: Persistent log storage for batch processing
3. **Consistent Formatting**: Standardized log format across all modules
4. **Flexible Configuration**: Runtime log level and output adjustment
5. **Terminal Detection**: Smart color support based on terminal capabilities

### Critical Dependencies
- **logging**: Python standard library logging module
- **sys**: System-specific parameters and functions
- **pathlib**: Modern path handling for log files
- **os**: Operating system interface for directory operations

## Logging Architecture

### Hierarchical Structure
1. **Root Logger Configuration**:
   - Centralized level management
   - Handler coordination and setup
   - Format standardization across pipeline

2. **Module-Level Loggers**:
   - Named loggers for each module (`__name__`)
   - Inherited configuration from root logger
   - Individual level control capability

3. **Handler Types**:
   - **Console Handler**: Real-time progress monitoring
   - **File Handler**: Persistent record keeping
   - **Custom Colored Formatter**: Enhanced visual readability

### Colored Formatter System

#### Visual Log Level Distinction
Uses ANSI color codes for immediate visual recognition:

| Log Level | Color | Purpose | Use Case |
|-----------|-------|---------|----------|
| **DEBUG** | Cyan | Detailed diagnostic information | Development and troubleshooting |
| **INFO** | Green | General progress and success | Normal operational monitoring |
| **WARNING** | Yellow | Non-critical issues and alerts | Attention needed, not blocking |
| **ERROR** | Red | Critical errors requiring attention | Problems that need resolution |
| **CRITICAL** | Magenta | System-level failures | Serious issues requiring immediate action |

#### Color Code Implementation
```python
COLORS = {
    'DEBUG': '\033[36m',     # Cyan - Detailed technical information
    'INFO': '\033[32m',      # Green - Normal operations
    'WARNING': '\033[33m',    # Yellow - Caution needed
    'ERROR': '\033[31m',     # Red - Problems requiring attention
    'CRITICAL': '\033[35m',   # Magenta - Critical system issues
    'RESET': '\033[0m'       # Reset to default colors
}
```

### Terminal Compatibility

#### Smart Detection System
1. **TTY Detection**: Checks if output supports colors
2. **Environment Awareness**: Adapts to different terminal types
3. **Fallback Support**: Graceful degradation when colors unavailable
4. **Platform Handling**: Works across Windows, macOS, Linux

#### Compatibility Features
- Automatic color capability detection
- Graceful fallback to plain text when colors not supported
- Support for various terminal emulators
- CI/CD environment compatibility

### Log Format Standardization

#### Default Format
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

#### Example Output
```
2025-01-01 10:30:15 - extract_metadata - INFO - Metadata extracted: Song Title - Artist Name
2025-01-01 10:30:16 - separate_vocals - WARNING - Using CPU processing (GPU not available)
2025-01-01 10:30:17 - transcribe_vocals - ERROR - Transcription failed: Model timeout
```

#### Format Components
- **Timestamp**: ISO format with millisecond precision
- **Module Name**: Source module for context
- **Log Level**: Colored level indicator
- **Message**: Actual log content with context

## Configuration Flexibility

### Log Level Control
| Level | Numeric Value | Use Case | Verbosity |
|-------|---------------|----------|-----------|
| **DEBUG** | 10 | Development and troubleshooting | Maximum detail |
| **INFO** | 20 | Normal operational monitoring | Standard progress |
| **WARNING** | 30 | Issues requiring attention | Caution alerts |
| **ERROR** | 40 | Critical problems | Error conditions |
| **CRITICAL** | 50 | System failures | Emergency issues |

### Output Destinations
1. **Console Output**: Real-time monitoring and development feedback
2. **File Output**: Persistent logging for batch processing and analysis
3. **Dual Output**: Simultaneous console and file logging

### Formatting Options
- **Colored Console**: Enhanced readability with color coding
- **Plain File Format**: Clean text format for log files
- **Custom Formats**: Configurable format strings
- **Date Formatting**: Customizable timestamp formats

## Usage Patterns

### Basic Setup
```python
from logging_config import setup_logging, get_logger

# Basic logging setup
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Use in module
logger.info(f"Processing file: {file_path}")
logger.error(f"Failed to process: {error_message}")
```

### Advanced Configuration
```python
# Setup with file logging and colors
setup_logging(
    level=logging.DEBUG,
    log_file="processing.log",
    use_colors=True
)

# Module-specific logger
logger = get_logger(__name__)
logger.debug("Detailed processing information")
```

### Module-Level Control
```python
# Override global logging level for specific module
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)  # More verbose for this module only

# Use different levels appropriately
logger.debug("Variable values and internal state")
logger.info("Major processing steps and results")
logger.warning("Recoverable issues and fallbacks")
logger.error("Processing failures and exceptions")
```

## Integration Examples

### extract_metadata.py
```python
from logging_config import get_logger

logger = get_logger(__name__)
logger.info(f"Processing file: {file_path}")
logger.debug(f"Found tags: {tag_dict}")
logger.warning(f"Missing metadata for: {filename}")
```

### separate_vocals.py
```python
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)
logger.info(f"Loading audio file: {input_file_path}")
logger.info(f"Vocals extracted successfully: {output_path}")
logger.error(f"Failed to separate vocals: {error_message}")
```

### process_lyrics.py
```python
from logging_config import setup_logging, get_logger

# Setup logging for batch processing
setup_logging(level=log_level, use_colors=use_colors)
logger = get_logger(__name__)

logger.info(f"Starting batch processing for: {input_dir}")
logger.info(f"Found {len(files)} files to process")
```

## Error Handling & Edge Cases

### Configuration Issues
- **Invalid Log Levels**: Non-standard level specifications
- **Malformed Format Strings**: Invalid format string syntax
- **Unwritable Directories**: Log file directory permission issues
- **File Access Errors**: Log file creation or writing failures

### Terminal Issues
- **Non-TTY Environments**: CI/CD systems, scripts, redirects
- **Unsupported Terminals**: Limited terminal capability
- **Color Detection Failures**: Incorrect color capability assessment

### Handler Conflicts
- **Multiple Initialization**: Duplicate handler setup
- **Existing Handler Issues**: Conflicts with existing loggers
- **Resource Cleanup**: Handler removal and memory management

### Performance Issues
- **Logging Overhead**: Excessive logging impacting performance
- **Large Log Files**: File size management and rotation
- **Memory Usage**: Log message storage in verbose modes

## Performance Considerations

### Optimization Features
- **Minimal Overhead**: Negligible impact on processing speed
- **Efficient Formatting**: Fast color processing and formatting
- **Buffered I/O**: Efficient file writing for log files
- **Smart Detection**: Terminal capability checking avoids unnecessary operations

### Performance Characteristics
- **Processing Impact**: Negligible for normal logging levels
- **Memory Scaling**: Memory usage scales with log volume
- **Disk I/O**: File logging adds disk write operations
- **Network I/O**: None (local operations only)

## Logging Best Practices

### Appropriate Level Usage
1. **DEBUG Level**:
   - Detailed internal state and variable values
   - Complex logic flow and decision points
   - Performance metrics and timing information

2. **INFO Level**:
   - Major processing steps and milestones
   - Successful operations and results
   - Important state changes and progress

3. **WARNING Level**:
   - Recoverable issues and fallback usage
   - Deprecated functionality or API changes
   - Performance concerns or resource issues

4. **ERROR Level**:
   - Processing failures and exceptions
   - Critical errors preventing operation
   - Resource exhaustion or system issues

### Message Content Guidelines
- **Contextual Information**: Include file names, counts, identifiers
- **Actionable Content**: Provide information that helps troubleshooting
- **Security Awareness**: Avoid sensitive data in logs
- **Structured Data**: Use consistent format for complex information

### Performance Optimization
- **Lazy Evaluation**: Avoid expensive operations in log statements
- **Level Checking**: Check log levels before heavy computation
- **String Efficiency**: Use efficient string formatting
- **Batch Logging**: Group related log messages when appropriate

## Debugging Capabilities

### Enhanced Debugging Support
1. **Stack Trace Integration**:
   - Automatic exception information capture
   - Context preservation for error analysis
   - Chain of execution tracking

2. **Module-Level Debugging**:
   - Individual module log level control
   - Detailed operation tracing
   - Performance monitoring hooks

3. **Production Debugging**:
   - Structured log analysis capabilities
   - Error pattern identification
   - Performance bottleneck detection

### Debug Logging Examples
```python
# Detailed processing information
logger.debug(f"Processing tags: {tag_list}")
logger.debug(f"Priority calculation: {priority_dict}")
logger.debug(f"File size: {file_size_bytes} bytes")

# Performance monitoring
import time
start_time = time.time()
# ... processing ...
logger.debug(f"Processing took: {time.time() - start_time:.3f} seconds")

# Complex data structure logging
logger.debug(f"Configuration: {json.dumps(config_dict, indent=2)}")
```

## Maintenance & Development

### Configuration Updates
- **Color Scheme Updates**: Maintain current color standards
- **Format Evolution**: Update format strings as needed
- **Terminal Support**: Add support for new terminal types
- **Performance Monitoring**: Track logging system performance

### Best Practices Updates
- **Level Usage Review**: Regular review of logging level usage
- **Message Quality**: Maintain high-quality log messages
- **Performance Impact**: Monitor logging performance overhead
- **Security Review**: Regular review of logged information

### Adding New Features
1. **Custom Formatters**: Add specialized formatting options
2. **Handler Types**: Implement new output destinations
3. **Filter Systems**: Add advanced log filtering capabilities
4. **Integration Options**: Support for external logging systems

## Troubleshooting Guide

### Quick Diagnostics
```python
# Test basic logging setup
from logging_config import setup_logging, get_logger

setup_logging(level=logging.INFO)
logger = get_logger(__name__)
logger.info("Logging test message")

# Test file logging
setup_logging(level=logging.DEBUG, log_file="test.log")
logger.debug("Debug message for file")
```

### Common Solutions
1. **No log output**: Check log level settings, verify handler configuration
2. **Colors not displaying**: Check terminal capabilities, verify TTY detection
3. **Log file not created**: Check directory permissions, verify path accessibility
4. **Performance impact**: Adjust log levels, review message frequency

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Utils Module](utils.md) - Shared utility functions
- [Main Interface](main.md) - Command-line interface module
- [Individual Processing Modules](*.md) - Module-specific documentation