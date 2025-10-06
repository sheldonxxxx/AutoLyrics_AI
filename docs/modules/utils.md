# Utilities Module

## 🔧 Shared Utility Functions (`utils.py`)

Provides essential utility functions used throughout the Music Lyrics Processing Pipeline. This module handles file operations, path management, data validation, environment configuration, and various helper functions that support the core processing modules, ensuring consistent behavior and reducing code duplication.

## Pipeline Integration

```
All Pipeline       ┌──────────────────┐    All Pipeline
Modules     ◀────▶ │  utils.py        │ ◀────▶ Modules
                    │  (shared         │
                    │  utilities)      │
                    └──────────────────┘
```

## Core Functionality Areas

### 1. File System Operations
- **Path Management**: Directory creation, path validation, structure preservation
- **File Discovery**: Recursive audio file finding across directory trees
- **I/O Helpers**: Safe file reading/writing with proper encoding

### 2. Data Processing
- **Text Parsing**: LRC and transcript format conversion
- **Content Extraction**: Lyrics processing and metadata removal
- **Format Validation**: LRC structure and timestamp verification

### 3. Configuration Management
- **Environment Variables**: Validation and fallback mechanisms
- **API Settings**: OpenAI and translation service configuration
- **Language Support**: Prompt file mapping for different languages

### 4. Output Management
- **CSV Generation**: Comprehensive processing reports
- **Directory Handling**: Cross-platform path operations
- **Result Aggregation**: Batch processing result collection

### 5. Content Processing
- **LRC/Transcript Parsing**: Format conversion and manipulation
- **Timestamp Conversion**: ASR format to LRC format transformation
- **Resume Support**: Skip logic for completed files

## Technical Implementation

### Dependencies
- **pathlib**: Modern Python path handling (Python 3.4+)
- **typing**: Type hints for better code documentation
- **logging_config**: Consistent logging across pipeline
- **csv**: Standard library for CSV file generation

## File System Utilities

### Audio File Discovery
#### `find_audio_files()`
Recursively finds all audio files in directory tree.

**Parameters:**
- `input_dir` (str): Directory to search for audio files

**Returns:**
- `List[Path]`: List of audio file paths found (FLAC and MP3)

**Features:**
- Supports nested directory structures
- Finds both FLAC and MP3 formats
- Comprehensive logging of discovery results

#### `find_flac_files()`
Specialized function for FLAC-only file discovery.

**Parameters:**
- `input_dir` (str): Directory to search for FLAC files

**Returns:**
- `List[Path]`: List of FLAC file paths found

### Path Management
#### `get_output_paths()`
Generates organized output file paths preserving folder structure.

**Parameters:**
- `input_file` (Path): Input audio file path
- `output_dir` (str): Output directory for final files
- `temp_dir` (str): Temporary directory for intermediate files
- `input_base_dir` (str): Base input directory for relative path calculation

**Returns:**
- `dict`: Dictionary containing all output file paths

**Path Organization:**
```python
{
    'vocals_wav': 'tmp/album/song/song_(Vocals)_UVR_MDXNET_Main.wav',
    'transcript_txt': 'tmp/album/song/song_(Vocals)_UVR_MDXNET_Main_transcript.txt',
    'lyrics_txt': 'tmp/album/song/song_lyrics.txt',
    'lrc': 'tmp/album/song/song.lrc',
    'translated_lrc': 'output/album/song.lrc'
}
```

#### `ensure_output_directory()`
Creates output directories safely with error handling.

**Parameters:**
- `output_dir` (str): Directory path to create

**Returns:**
- `bool`: True if directory exists or was created successfully

### File I/O Operations
#### Text File Readers
- **`read_lrc_file()`**: Reads LRC files with UTF-8 encoding
- **`read_lyrics_file()`**: Reads lyrics with metadata preservation
- **`read_transcript_file()`**: Reads ASR transcript files
- **`load_prompt_template()`**: Loads LLM prompt templates

#### Safe I/O Features
- Proper UTF-8 encoding handling
- Error handling for missing or corrupted files
- Consistent encoding across all operations

## Data Processing Utilities

### Transcript Processing
#### `parse_transcript_segments()`
Converts transcript text back to segment objects.

**Parameters:**
- `transcript_content` (str): Transcript content with timestamp format

**Returns:**
- `List[SimpleNamespace]`: List of transcript segments with start, end, text

#### `convert_transcript_to_lrc()`
Transforms ASR transcript format to LRC format.

**Parameters:**
- `transcript_text` (str): ASR transcript with timestamps

**Returns:**
- `str`: Transcript converted to LRC format

**Timestamp Conversion:**
```
ASR Format: [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
LRC Format: [00:00.92]ああ 素晴らしき世界に今日も乾杯
```

### Content Extraction
#### `extract_lyrics_content()`
Removes headers and metadata from lyrics files.

**Parameters:**
- `lyrics_content` (str): Raw lyrics content from file

**Returns:**
- `str`: Extracted lyrics content without headers

**Processing:**
- Identifies header sections (marked with "=" * 10)
- Extracts only actual lyrics content
- Preserves line breaks and formatting

### Validation Functions
#### `validate_lrc_content()`
Ensures LRC content follows proper format.

**Parameters:**
- `content` (str): LRC content to validate

**Returns:**
- `bool`: True if content is valid LRC format

**Validation Checks:**
- Non-empty content verification
- Proper timestamp format detection
- LRC structure compliance

#### `should_skip_file()`
Supports resume functionality by checking completion status.

**Parameters:**
- `paths` (dict): Dictionary of file paths to check
- `resume` (bool): Whether resume mode is enabled

**Returns:**
- `bool`: True if essential files exist and should be skipped

## Configuration Management

### Environment Variable Validation
#### `validate_environment_variables()`
Validates required environment variables with fallback support.

**Parameters:**
- `required_vars` (List[str]): List of required variable names
- `optional_vars` (Optional[Dict[str, str]]): Optional variables with defaults

**Returns:**
- `Dict[str, str]`: Dictionary of validated environment variables

**Raises:**
- `ValueError`: If any required environment variable is not set

### API Configuration
#### `get_openai_config()`
Retrieves general OpenAI API configuration.

**Returns:**
- `Dict[str, str]`: Dictionary containing base_url, api_key, and model

**Required Variables:**
- `OPENAI_BASE_URL`: API endpoint URL
- `OPENAI_API_KEY`: API authentication key
- `OPENAI_MODEL`: Model name for processing

#### `get_translation_config()`
Retrieves translation-specific API configuration with fallbacks.

**Returns:**
- `Dict[str, str]`: Translation API configuration

**Configuration Hierarchy:**
1. Translation-specific variables (TRANSLATION_*)
2. Fallback to general OpenAI variables (OPENAI_*)
3. Error if neither is available

### Language Support
#### `get_prompt_file_for_language()`
Maps target languages to appropriate prompt files.

**Parameters:**
- `target_language` (str): Target language for translation

**Returns:**
- `str`: Prompt file name for the specified language

**Current Mapping:**
```python
{
    "Traditional Chinese": "lrc_traditional_chinese_prompt.txt",
    # Extensible for future languages
}
```

## CSV Output System

### Comprehensive Reporting
#### `write_csv_results()`
Generates detailed processing reports in CSV format.

**Parameters:**
- `csv_file_path` (str): Path for output CSV file
- `results` (list): List of processing result dictionaries

**Returns:**
- `bool`: True if CSV writing was successful

### CSV Structure
**Column Categories:**
- **File Information**: filename, file_path, processing timestamps
- **Metadata Results**: title, artist, album, genre, year, track_number
- **Audio Processing**: vocal separation, transcription metrics
- **Quality Assurance**: verification confidence, LRC generation results
- **Error Reporting**: error messages and troubleshooting data

**Example Output:**
```csv
filename,processing_start_time,metadata_success,vocals_separation_success,...
song1.flac,2025-01-01T10:00:00,True,True,...
song2.flac,2025-01-01T10:05:00,True,False,"Failed to separate vocals"
```

## Error Handling & Edge Cases

### File System Issues
- **Missing Directories**: Input/output paths don't exist
- **Permission Errors**: Insufficient access to files/directories
- **Disk Space**: Insufficient space for processing operations
- **Path Length**: OS-specific path length limitations

### Data Format Issues
- **Malformed Files**: Corrupted transcript or LRC files
- **Unexpected Formats**: Non-standard timestamp formats
- **Encoding Problems**: Character encoding mismatches
- **File Corruption**: Truncated or corrupted file content

### Configuration Issues
- **Missing Variables**: Required environment variables not set
- **Invalid Endpoints**: Malformed API URLs or credentials
- **Language Support**: Unsupported language specifications
- **Template Issues**: Malformed or missing prompt templates

### Processing Issues
- **Memory Exhaustion**: Large files requiring too much RAM
- **Timeout Issues**: Long-running operations exceeding limits
- **Resource Conflicts**: Concurrent access issues in batch processing
- **Network Problems**: API connectivity issues

## Performance Considerations

### Optimization Features
- **Efficient Discovery**: Optimized recursive search with early termination
- **Memory Management**: Minimal memory usage for text operations
- **I/O Optimization**: Efficient buffered reading/writing
- **Path Caching**: Cached path calculations for repeated operations

### Performance Characteristics
- **File Operations**: Typically milliseconds per operation
- **Text Processing**: Minimal computational overhead
- **Directory Scaling**: Scales well with directory size
- **Batch Efficiency**: Optimized for batch processing scenarios

## Usage Examples

### File Operations
```python
from utils import find_audio_files, get_output_paths

# Discover audio files
files = find_audio_files("input")
print(f"Found {len(files)} audio files")

# Generate output paths
paths = get_output_paths(file, "output", "tmp")
print(f"Vocals will be saved to: {paths['vocals_wav']}")
```

### Data Processing
```python
from utils import read_transcript_file, convert_transcript_to_lrc

# Read and convert transcript
transcript = read_transcript_file("transcript.txt")
lrc_content = convert_transcript_to_lrc(transcript)

# Process lyrics content
from utils import extract_lyrics_content
raw_lyrics = read_lyrics_file("lyrics.txt")
clean_lyrics = extract_lyrics_content(raw_lyrics)
```

### Configuration Management
```python
from utils import get_openai_config, validate_environment_variables

# Validate required environment variables
try:
    config = get_openai_config()
    print(f"Using model: {config['OPENAI_MODEL']}")
except ValueError as e:
    print(f"Configuration error: {e}")

# Custom validation
validate_environment_variables(
    required_vars=["API_KEY", "BASE_URL"],
    optional_vars={"MODEL": "default-model"}
)
```

## API Reference

### File System Functions

#### `find_audio_files(input_dir: str) -> List[Path]`
Find all audio files (FLAC and MP3) recursively in directory.

#### `find_flac_files(input_dir: str) -> List[Path]`
Find all FLAC files recursively in directory.

#### `get_output_paths() -> dict`
Generate organized output file paths preserving folder structure.

#### `ensure_output_directory(output_dir: str) -> bool`
Create output directory if it doesn't exist.

### Data Processing Functions

#### `read_lrc_file(file_path: str) -> str`
Read LRC file content with UTF-8 encoding.

#### `read_lyrics_file(file_path: str) -> str`
Read lyrics file content preserving metadata.

#### `read_transcript_file(file_path: str) -> str`
Read ASR transcript file content.

#### `load_prompt_template(prompt_file_path: str) -> str | None`
Load LLM prompt template from file.

#### `validate_lrc_content(content: str) -> bool`
Validate LRC content format compliance.

#### `convert_transcript_to_lrc(transcript_text: str) -> str`
Convert ASR transcript format to LRC format.

#### `parse_transcript_segments() -> List[SimpleNamespace]`
Parse transcript content back to segment objects.

#### `should_skip_file(paths: dict, resume: bool) -> bool`
Check if file should be skipped in resume mode.

#### `extract_lyrics_content(lyrics_content: str) -> str`
Extract actual lyrics from formatted lyrics file.

### Configuration Functions

#### `get_prompt_file_for_language(target_language: str) -> str`
Get appropriate prompt file for target language.

#### `write_csv_results(csv_file_path: str, results: list) -> bool`
Write processing results to CSV file.

#### `validate_environment_variables() -> Dict[str, str]`
Validate required environment variables.

#### `get_openai_config() -> Dict[str, str]`
Get OpenAI API configuration with validation.

#### `get_translation_config() -> Dict[str, str]`
Get translation API configuration with fallbacks.

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed file operations and path calculations
- **INFO**: Successful operations and file discoveries
- **WARNING**: Fallback behaviors and minor issues
- **ERROR**: Critical failures preventing operations

### Example Log Output
```
INFO - Found 15 audio files in input directory
INFO - Created output directory structure: tmp/song1/
WARNING - Input file not relative to base dir, using flat structure
ERROR - Failed to create output directory: Permission denied
```

## Testing & Validation

### Test Coverage
- File discovery across various directory structures
- Path generation with folder hierarchy preservation
- Timestamp conversion accuracy verification
- Configuration validation with missing variables
- CSV generation with various data types and edge cases

### Validation Checklist
- [ ] File discovery works across different directory structures
- [ ] Path generation preserves folder hierarchy correctly
- [ ] Timestamp conversion maintains accuracy
- [ ] Configuration validation handles missing variables appropriately
- [ ] CSV generation works with various result data types

## Common Pitfalls & Solutions

### Issue: "File not found errors"
**Symptoms:** Functions return empty results or error on missing files
**Causes:**
- Incorrect file paths or working directory
- Files don't exist or were moved
- Permission issues preventing file access
**Solutions:**
- Verify file paths and working directory
- Check file existence with `ls` or `dir`
- Verify read permissions on files and directories

### Issue: "Permission denied"
**Symptoms:** Cannot read or write files despite existing paths
**Causes:**
- Insufficient file or directory permissions
- Files opened by other applications
- Network drive access restrictions
**Solutions:**
- Check permissions with `ls -l` (Unix) or file properties (Windows)
- Close applications that might have files open
- Verify network drive connectivity and permissions

### Issue: "Out of memory on large directories"
**Symptoms:** Processing fails with memory errors on large file collections
**Causes:**
- Too many files to process in available RAM
- Memory leaks in processing pipeline
- System resource exhaustion
**Solutions:**
- Process directories in smaller batches
- Increase system RAM if possible
- Monitor memory usage during processing

### Issue: "CSV generation failed"
**Symptoms:** Processing completes but CSV report not created
**Causes:**
- File permission issues on output directory
- Disk space exhaustion during writing
- Data format issues causing write failures
**Solutions:**
- Check write permissions on output directory
- Verify available disk space
- Review data format for CSV compatibility

## Maintenance & Development

### Adding New Audio Formats
1. **Update Discovery Functions**: Add new extensions to search patterns
2. **Test Compatibility**: Verify new formats work with existing pipeline
3. **Update Documentation**: Document new format support
4. **Performance Testing**: Ensure new formats don't impact performance

### CSV Format Evolution
1. **Column Management**: Add new columns as pipeline metrics evolve
2. **Backward Compatibility**: Maintain compatibility with existing reports
3. **Data Type Handling**: Ensure proper handling of new data types
4. **Documentation Updates**: Keep CSV format documentation current

### Performance Optimization
- **Discovery Optimization**: Improve file search patterns
- **Memory Management**: Optimize memory usage for large operations
- **I/O Efficiency**: Enhance file reading/writing performance
- **Caching Strategies**: Implement result caching where beneficial

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test file discovery
python -c "
from utils import find_audio_files
files = find_audio_files('input')
print(f'Found {len(files)} files')
"

# Test path generation
python -c "
from utils import get_output_paths
from pathlib import Path
paths = get_output_paths(Path('input/song.flac'))
print('Generated paths:', paths)
"

# Test configuration
python -c "
from utils import get_openai_config
try:
    config = get_openai_config()
    print('Configuration valid')
except ValueError as e:
    print(f'Configuration error: {e}')
"
```

### Common Solutions
1. **Path Issues**: Use absolute paths, verify working directory
2. **Permission Issues**: Check file/directory permissions with system tools
3. **Memory Issues**: Monitor resource usage, process in smaller batches
4. **Configuration Issues**: Verify environment variables and file paths

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Process Lyrics Module](process_lyrics.md) - Batch processing orchestrator
- [Main Interface](main.md) - Command-line interface module
- [Logging Configuration](logging_config.md) - Centralized logging system