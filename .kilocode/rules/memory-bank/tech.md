# Technology: Music Lyrics Processing Pipeline

## Core Technologies

### Python 3.13+
Modern Python version providing latest language features and performance improvements.

### Audio Processing Libraries
- **audio-separator**: Vocal separation using UVR models (CPU-based)
- **faster-whisper**: ASR transcription with word-level timestamps (CPU-compatible)

### Metadata Extraction
- **mutagen**: Audio metadata extraction with multiple format support

### API Integration
- **Pydantic AI**: Structured LLM interactions for LRC generation and translation
- **python-dotenv**: Environment variable management

### Package Management
- **uv**: Modern Python package manager for dependency management

## Development Tools and Practices

### Running Python Code
- **Always use `uv run` to execute Python scripts** instead of direct `python` or `python3` commands
- This ensures the correct virtual environment and dependencies are used

### Logging Framework
- **logging module**: Built-in Python logging with centralized configuration
- **utils/logging_config.py**: Centralized logging setup across all modules

### File Path Management
- **pathlib**: Modern Python path handling with Path objects
- **utils.py**: Centralized utility functions for file operations

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
- faster-whisper>=1.2.0
- mutagen>=1.47.0
- pydantic-ai>=1.0.15
- python-dotenv>=1.1.1
- requests>=2.32.5

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