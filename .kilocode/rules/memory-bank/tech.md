# Technology: Music Lyrics Processing Pipeline

## Core Technologies

### Python 3.13+
The project is built on Python 3.13+ as specified in the pyproject.toml, providing access to the latest language features and performance improvements.

### Audio Processing Libraries
- **audio-separator**: Used for vocal separation using UVR models
  - CPU-based processing for compatibility
  - Uses UVR_MDXNET_Main model by default
  - Handles multiple audio formats (FLAC, MP3, etc.)

- **faster-whisper**: Used for ASR (Automatic Speech Recognition) transcription
  - Provides timestamped transcription with word-level accuracy
 - CPU-compatible models for broad accessibility
 - Supports various model sizes (large-v3-turbo, etc.)

### Metadata Extraction
- **mutagen**: Used for extracting metadata from audio files
  - Supports multiple formats (FLAC, MP3, ID3, etc.)
  - Handles various tag formats and structures
  - Provides fallback to filename parsing when tags are missing

### Web Scraping
- **requests**: Used for HTTP requests to lyric websites
- **beautifulsoup4**: Used for parsing HTML content from lyric websites
  - Specifically targets uta-net.com for Japanese lyrics
  - Handles various page structures and content formats

### API Integration
- **OpenAI-compatible client**: Used for LRC generation and translation
  - Supports custom base URLs for alternative providers
  - Environment variable configuration for API keys and endpoints
  - Handles Qwen models specifically (Qwen/Qwen3-235B-A22B-Instruct-2507)

### Environment Management
- **python-dotenv**: Used for environment variable management
- **uv**: Package manager for Python dependencies

## Development Tools and Practices

### Package Management
- **uv**: Modern Python package manager used for dependency management
- **pyproject.toml**: Standard Python project configuration file
- **uv.lock**: Lock file for reproducible builds

### Logging Framework
- **logging module**: Built-in Python logging with centralized configuration
- **logging_config.py**: Centralized logging setup across all modules
 - UTF-8 encoding for international characters
 - Consistent formatting across components
  - Support for both console and file output

### Command-Line Interface
- **argparse**: Standard Python library for command-line argument parsing
- **Multiple entry points**: Individual scripts and main orchestrator

### File Path Management
- **pathlib**: Modern Python path handling with Path objects
- **utils.py**: Centralized utility functions for file operations
  - Recursive file discovery
  - Output path generation
  - Directory creation utilities

## Technical Constraints

### Processing Constraints
- CPU-based processing for broad compatibility
- Sequential processing pipeline (not parallelized)
- Large memory requirements for audio processing and models

### API Constraints
- Requires OpenAI-compatible API key for LRC generation and translation
- Rate limits may apply depending on API provider
- Model-specific token limits may affect processing of long lyrics

### Audio Format Constraints
- Primary focus on FLAC files (though other formats supported)
- Quality loss possible during vocal separation
- Large file sizes during intermediate processing steps

## Dependencies

### Core Dependencies
- audio-separator[cpu]>=0.39.0
- beautifulsoup4>=4.14.2
- faster-whisper>=1.2.0
- mutagen>=1.47.0
- openai>=2.0.1
- python-dotenv>=1.1.1
- requests>=2.32.5

### Development Dependencies
- uv (package manager)

## Configuration Management

### Environment Variables
- OPENAI_API_KEY: API key for OpenAI-compatible service
- OPENAI_BASE_URL: Base URL for OpenAI-compatible API
- OPENAI_MODEL: Model name for LRC generation
- TRANSLATION_MODEL: Model name for translation (defaults to OPENAI_MODEL)

### Directory Structure
- input/: Input audio files
- output/: Final LRC files
- tmp/: Temporary intermediate files
- models/: Audio separation models