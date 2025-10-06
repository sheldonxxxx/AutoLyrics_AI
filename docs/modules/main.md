# Main Interface Module

## 🎮 Command-Line Interface (`main.py`)

Serves as the primary entry point and command-line interface for the Music Lyrics Processing Pipeline. This module provides a unified interface for accessing individual pipeline components and orchestrating complex multi-step workflows, enabling both modular component testing and development workflow management.

## Pipeline Integration

```
Command Line       ┌──────────────────┐    Individual
Interface    ───▶ │  main.py         │ ───▶ Modules
                  │  (orchestrator)  │
                  └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Provide unified command-line interface for all pipeline operations
- Enable modular testing of individual pipeline components
- Route commands to appropriate module functions
- Handle centralized error management and reporting
- Manage logging and environment configuration

### Key Features
- **Action-Based Interface**: Six main actions for different operations
- **Module Coordination**: Dynamic loading and coordination of pipeline modules
- **Error Handling**: Centralized error management and user feedback
- **Development Support**: Individual component testing capabilities
- **Configuration Management**: Logging and environment setup

## Supported Actions

### 1. Overview Action
**Purpose**: Display system information and available actions
```bash
python main.py
# or
python main.py overview
```

**Output**: Shows available actions and usage examples

### 2. Metadata Action
**Purpose**: Extract metadata from individual audio files
```bash
python main.py metadata --file song.flac
```

**Process**:
- Loads `extract_metadata` module
- Extracts song information from audio tags
- Displays results in formatted output
- Useful for testing metadata extraction

### 3. Search Action
**Purpose**: Search for lyrics using metadata information
```bash
python main.py search --file song.flac
```

**Process**:
- Extracts metadata from audio file
- Uses `search_lyrics` module to find lyrics
- Saves results to output directory
- Tests lyrics search functionality

### 4. Separate Action
**Purpose**: Separate vocals and perform ASR transcription
```bash
python main.py separate --file song.flac
```

**Process**:
- Uses `separate_vocals` for vocal isolation
- Uses `transcribe_vocals` for ASR transcription
- Saves both vocals and transcript files
- Tests complete vocal processing pipeline

### 5. Generate Action
**Purpose**: Generate LRC files from lyrics and transcripts
```bash
python main.py generate --file song.flac
```

**Process**:
- Reads existing lyrics and transcript files
- Uses `generate_lrc` module for LRC creation
- Saves synchronized LRC file
- Tests LRC generation capabilities

### 6. Translate Action
**Purpose**: Translate LRC files to Traditional Chinese
```bash
python main.py translate --file song.lrc
```

**Process**:
- Uses `translate_lrc` module for translation
- Creates bilingual LRC file
- Preserves timing and formatting
- Tests translation functionality

## Command-Line Interface

### Basic Syntax
```bash
python main.py [action] [options]
```

### Argument Handling
- **action**: Primary operation to perform (default: 'overview')
- **--file, -f**: Input audio file path for file-based actions
- **--log-level**: Logging level (DEBUG, INFO, WARNING, ERROR)

### Action Routing Architecture
Each action follows consistent execution pattern:

1. **Input Validation**: Verify file exists and is accessible
2. **Module Import**: Dynamically load required modules
3. **Function Execution**: Call appropriate module functions
4. **Result Processing**: Handle and display results
5. **File Output**: Save results to appropriate locations

## Module Coordination

### Dependency Management
Manages complex dependencies between pipeline modules:

| Action | Required Modules | Purpose |
|--------|------------------|---------|
| **metadata** | `extract_metadata` | Song information extraction |
| **search** | `extract_metadata`, `search_lyrics` | Lyrics discovery |
| **separate** | `separate_vocals`, `transcribe_vocals` | Vocal processing |
| **generate** | `generate_lrc` | LRC file creation |
| **translate** | `translate_lrc` | Bilingual translation |

### Dynamic Module Loading
- **Runtime Import**: Loads modules only when needed
- **Error Isolation**: Module failures don't crash entire interface
- **Dependency Resolution**: Handles complex module interdependencies
- **Version Compatibility**: Works with module interface changes

## File Path Conventions

### Input Files
- **Audio Files**: Various formats (FLAC, MP3, etc.)
- **Expected Location**: Current directory or specified via `--file`
- **Validation**: File existence and accessibility checks

### Output Files
Standardized output locations for consistency:

| File Type | Location | Naming Pattern |
|-----------|----------|----------------|
| **Lyrics** | `output/` | `{filename}_lyrics.txt` |
| **Transcripts** | `output/` | `{filename}_(Vocals)_UVR_MDXNET_Main_transcript.txt` |
| **LRC Files** | `output/` | `{filename}.lrc` |
| **Translated LRC** | `output/` | `{filename}_Traditional_Chinese.lrc` |

## Error Handling & Edge Cases

### File System Issues
- **Missing Files**: Input files don't exist or moved
- **Permission Errors**: Insufficient access to files/directories
- **Disk Space**: Insufficient space for output files

### Module Import Issues
- **Missing Dependencies**: Required modules not installed
- **Version Conflicts**: Incompatible module versions
- **Import Errors**: Circular imports or syntax issues

### Action-Specific Issues
- **Invalid Parameters**: Wrong arguments for specific actions
- **Missing Prerequisites**: Required files for complex actions
- **Resource Requirements**: Insufficient resources for operations

### Configuration Issues
- **Environment Variables**: Missing or invalid configuration
- **Logging Setup**: Logging configuration failures
- **API Configuration**: Invalid API settings or credentials

## Performance Considerations

### Processing Speed by Action
| Action | Typical Speed | Factors |
|--------|---------------|---------|
| **overview** | Instantaneous | Just displays help text |
| **metadata** | Fast | Seconds per file, metadata only |
| **search** | Moderate | Depends on network and API speed |
| **separate** | Slow | Minutes per file, CPU intensive |
| **generate** | Moderate | Depends on LLM API response time |
| **translate** | Moderate | Depends on translation API speed |

### Optimization Features
- **Fast Action Routing**: Quick dispatch to appropriate modules
- **Minimal Overhead**: Low resource usage for simple operations
- **Efficient Module Loading**: Dynamic imports reduce memory usage
- **Smart Caching**: Leverages existing module caching systems

## Usage Patterns

### Development and Testing
```bash
# Test individual components during development
python main.py metadata --file test.flac
python main.py search --file test.flac

# Debug with detailed logging
python main.py --log-level DEBUG metadata --file song.flac

# Test vocal processing pipeline
python main.py separate --file song.flac
```

### Production Processing
```bash
# Process complete workflow for individual files
python main.py separate --file song.flac
python main.py generate --file song.flac
python main.py translate --file song.lrc

# Use batch processor for multiple files
python process_lyrics.py input_directory
```

### Batch Processing
```bash
# Use process_lyrics.py for batch operations
python process_lyrics.py /path/to/music/library

# Resume interrupted batch processing
python process_lyrics.py --resume

# Generate detailed processing reports
python process_lyrics.py --csv-output results.csv
```

### Debugging and Troubleshooting
```bash
# Enable debug logging for detailed information
python main.py --log-level DEBUG metadata --file song.flac

# Test with known good files
python main.py metadata --file known_good.flac

# Isolate specific components
python main.py search --file test.flac  # Test search functionality
python main.py separate --file test.flac  # Test vocal processing
```

## Component Testing

### Individual Module Testing
Enables isolated testing of pipeline components:

- **Metadata Extraction**: Test tag reading and parsing accuracy
- **Lyrics Search**: Verify search functionality and result quality
- **Vocal Separation**: Validate audio processing and cleanup
- **ASR Transcription**: Check speech recognition accuracy
- **LRC Generation**: Test lyrics-to-timing alignment
- **Translation**: Confirm translation quality and format

### Integration Testing
Supports end-to-end workflow validation:

- **Action Chaining**: Test multiple actions in sequence
- **Data Flow Verification**: Ensure data passes correctly between modules
- **Error Recovery**: Test error handling and recovery mechanisms
- **Output Validation**: Verify final output quality and format

## Maintenance & Development

### Adding New Actions
1. **Action Definition**: Add new action to argument parser choices
2. **Handler Implementation**: Create action handling logic
3. **Module Integration**: Integrate with appropriate pipeline modules
4. **Documentation Updates**: Update help text and documentation

### Module Interface Changes
- **Compatibility Maintenance**: Ensure compatibility with module changes
- **Version Tracking**: Monitor module interface evolution
- **Testing Updates**: Update tests for interface changes
- **Documentation Sync**: Keep documentation current with interfaces

### Performance Monitoring
- **Action Success Rates**: Monitor success/failure rates by action
- **Processing Times**: Track performance for different file types
- **Error Patterns**: Identify common failure modes
- **Resource Usage**: Monitor memory and CPU usage patterns

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test basic functionality
python main.py overview

# Test with known good file
python main.py metadata --file known_good.flac

# Enable debug logging
python main.py --log-level DEBUG metadata --file problem_file.flac
```

### Common Solutions

#### Issue: "Module import errors"
**Symptoms:** ImportError or ModuleNotFoundError when running actions
**Causes:**
- Missing Python packages or dependencies
- Incorrect Python path or environment
- Version conflicts between packages
**Solutions:**
- Check dependencies with `uv sync`
- Verify Python environment and virtual environment
- Reinstall requirements if needed

#### Issue: "File not found errors"
**Symptoms:** Actions fail with "file not found" messages
**Causes:**
- Incorrect file path or working directory
- File doesn't exist or was moved
- Permission issues preventing file access
**Solutions:**
- Verify file path and working directory
- Check file existence with `ls` or `dir`
- Confirm read permissions on file

#### Issue: "Permission denied"
**Symptoms:** Cannot access files or directories
**Causes:**
- Insufficient file or directory permissions
- Files opened by other applications
- Network drive access restrictions
**Solutions:**
- Check permissions with `ls -l` (Unix) or file properties (Windows)
- Close applications that might have files open
- Verify network drive connectivity and permissions

#### Issue: "Action failed"
**Symptoms:** Actions complete but with error status
**Causes:**
- Invalid parameters for specific actions
- Missing prerequisites or dependencies
- Resource limitations or timeouts
**Solutions:**
- Check logs for detailed error information
- Verify all prerequisites are met
- Review system resources and limitations

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Process Lyrics Module](process_lyrics.md) - Batch processing orchestrator
- [Utils Module](utils.md) - Shared utility functions
- [Logging Configuration](logging_config.md) - Centralized logging system