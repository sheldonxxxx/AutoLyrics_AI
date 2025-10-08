# Music Lyrics Processing Pipeline

## 🎵 Comprehensive Music Lyrics Automation System

The Music Lyrics Processing Pipeline is an advanced Python-based system that automates the complete process of creating synchronized, translated lyrics from audio files. This project combines multiple AI technologies to extract vocals, transcribe speech, search for lyrics, and generate professional-quality LRC files with translations.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- UV package manager
- Audio files (FLAC, MP3, WAV, M4A)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd music-lyric

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Basic Usage
```bash
# Process all audio files in input directory
uv run python process_lyrics.py

# Process with custom directories
uv run python process_lyrics.py /path/to/music --output-dir /path/to/output

# Resume interrupted processing
uv run python process_lyrics.py --resume
```

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Modules](#modules)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)

## 🎯 Overview

### What This Project Does

The Music Lyrics Processing Pipeline automates the complex process of creating synchronized lyrics for music files:

1. **Metadata Extraction** - Extracts song information from audio file tags
2. **Vocal Separation** - Uses AI to isolate vocals from background music
3. **Speech Recognition** - Transcribes vocals with precise timestamps
4. **Lyrics Search** - Finds matching lyrics from online databases
5. **Quality Verification** - Ensures lyrics match the audio content
6. **LRC Generation** - Creates synchronized LRC files with timing
7. **Translation** - Translates lyrics to Traditional Chinese

### Key Features

- **🤖 AI-Powered Processing** - Multiple AI technologies working together
- **🔄 Batch Processing** - Handle entire music libraries automatically
- **🎯 High Accuracy** - Quality verification and confidence scoring
- **🌍 Multi-Language** - Traditional Chinese translation support
- **📁 Smart Organization** - Preserves folder structure and metadata
- **🔧 Modular Design** - Individual components can be used separately
- **📊 Progress Tracking** - Detailed reporting and CSV export
- **💾 Resume Support** - Continue interrupted processing seamlessly

### Use Cases

- **Music Players** - Generate synchronized lyrics for media players
- **Karaoke Systems** - Create timed lyrics for karaoke applications
- **Accessibility Tools** - Provide lyrics for hearing-impaired users
- **Music Libraries** - Process large collections automatically
- **Content Creation** - Generate lyrics for music content creators

## 🏗️ Architecture

### System Architecture

```
Input Audio Files
       ↓
[Metadata Extraction] → Extract song title, artist, album
       ↓ (if no metadata)
[Song Identification] → Identify from ASR transcript (with retry)
       ↓
[Lyrics Search] → Search uta-net.com for matching lyrics
       ↓
[Lyrics Verification] → Verify lyrics match ASR content using LLM
       ↓ (if verification passes)
[LRC Generation] → Combine verified lyrics with ASR timestamps
       ↓
[Translation] → Translate to Traditional Chinese (bilingual output)
       ↓
Output: Synchronized bilingual LRC files
```

### Core Modules

| Module | Purpose | Key Technology |
|--------|---------|----------------|
| `extract_metadata` | Extract song info from audio tags | mutagen |
| `identify_song` | Identify songs from ASR transcripts | LLM + Web Search |
| `search_lyrics` | Find lyrics on uta-net.com | BeautifulSoup + requests |
| `verify_lyrics` | Verify lyrics match audio content | LLM Analysis |
| `separate_vocals` | Isolate vocals from music | audio-separator (UVR) |
| `transcribe_vocals` | Generate timestamped transcripts | faster-whisper |
| `generate_lrc` | Create synchronized LRC files | LLM Alignment |
| `translate_lrc` | Translate to Traditional Chinese | LLM Translation |
| `process_lyrics` | Orchestrate complete workflow | Batch Processing |
| `utils` | Shared utility functions | File I/O, Validation |
| `logging_config` | Centralized logging system | Python logging |

### Data Flow

#### File Organization
```
input/                    # Source audio files
tmp/{relative_path}/      # Processing intermediate files
    └── {filename}/
        ├── {filename}_(Vocals)_UVR_MDXNET_Main.wav
        ├── {filename}_(Vocals)_UVR_MDXNET_Main_transcript.txt
        ├── {filename}_lyrics.txt
        └── {filename}.lrc
output/{relative_path}/   # Final bilingual LRC files
    └── {filename}.lrc
```

## 📦 Installation

### System Requirements

- **Operating System**: macOS, Linux, or Windows
- **Python Version**: 3.13 or higher
- **RAM**: 4GB minimum, 8GB+ recommended
- **Disk Space**: 2GB+ for models and processing
- **Network**: Internet connection for API calls and model downloads

### Dependencies

#### Core Dependencies
- `audio-separator[cpu]>=0.39.0` - Vocal separation
- `faster-whisper>=1.2.0` - Speech recognition
- `mutagen>=1.47.0` - Audio metadata extraction
- `beautifulsoup4>=4.14.2` - Web scraping
- `requests>=2.32.5` - HTTP requests
- `openai>=2.0.1` - LLM API client
- `python-dotenv>=1.1.1` - Environment management

#### Development Tools
- `uv` - Python package manager

### Setup Instructions

1. **Install UV Package Manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Setup Project**
   ```bash
   git clone <repository-url>
   cd music-lyric
   uv sync
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Download Required Models**
   ```bash
   # Models are downloaded automatically on first use
   uv run python -c "from separate_vocals import separate_vocals; print('Models ready')"
   ```

## ⚙️ Configuration

### Environment Variables

#### Required Variables
```bash
# OpenAI-compatible API configuration
OPENAI_BASE_URL=https://your-api-endpoint.com
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507

```

#### Optional Variables
```bash
# Translation-specific API (falls back to OPENAI_ if not set)
TRANSLATION_BASE_URL=https://translation-api-endpoint.com
TRANSLATION_API_KEY=your-translation-api-key
TRANSLATION_MODEL=translation-model-name

# Logging configuration
LOG_LEVEL=INFO
```

### Configuration Files

- **`.env`** - Environment variables and API keys
- **`pyproject.toml`** - Python project configuration and dependencies
- **`logging_config.py`** - Centralized logging configuration

## 🚀 Usage

### Command-Line Interface

#### Individual Module Testing
```bash
# Test metadata extraction
uv run python main.py metadata --file song.flac

# Search for lyrics
uv run python main.py search --file song.flac

# Separate vocals and transcribe
uv run python main.py separate --file song.flac

# Generate LRC file
uv run python main.py generate --file song.flac

# Translate to Traditional Chinese
uv run python main.py translate --file song.lrc
```

#### Batch Processing
```bash
# Process all files in input directory
uv run python process_lyrics.py

# Process with custom paths
uv run python process_lyrics.py /path/to/music \
  --output-dir /path/to/output \
  --temp-dir /path/to/temp

# Resume interrupted processing
uv run python process_lyrics.py --resume

# Generate detailed CSV report
uv run python process_lyrics.py --csv-output results.csv
```

### Programmatic Usage

#### Basic Module Usage
```python
from extract_metadata import extract_metadata
from search_lyrics import search_uta_net

# Extract metadata
metadata = extract_metadata("song.flac")
print(f"Title: {metadata['title']}, Artist: {metadata['artist']}")

# Search for lyrics
lyrics = search_uta_net(metadata['title'], metadata['artist'])
print(f"Found lyrics: {len(lyrics)} characters")
```

#### Complete Pipeline Example
```python
from process_lyrics import process_single_audio_file
from pathlib import Path

# Process single file
input_file = Path("input/song.flac")
success, results = process_single_audio_file(
    input_file,
    output_dir="output",
    temp_dir="tmp",
    resume=True
)

if success:
    print(f"Processing completed: {results['filename']}")
else:
    print(f"Processing failed: {results['error_message']}")
```

## 📚 Modules

### Core Processing Modules

#### 🎵 **Metadata Extraction** (`extract_metadata.py`)
Extracts song information from audio file tags with intelligent fallback to filename parsing.

**Key Features:**
- Multiple audio format support (FLAC, MP3, M4A, etc.)
- Intelligent tag priority system
- Filename fallback for missing metadata
- Comprehensive error handling

#### 🎯 **Song Identification** (`identify_song.py`)
Identifies songs from ASR transcripts using LLM analysis and web search with retry mechanisms.

**Key Features:**
- LLM-powered song matching
- Web search integration (SearXNG)
- Retry mechanism with feedback
- Confidence scoring and validation

#### 🌊 **Vocal Separation** (`separate_vocals.py`)
Uses AI-powered source separation to isolate vocals from background music.

**Key Features:**
- UVR model integration
- CPU-compatible processing
- Automatic cleanup of non-vocal files
- Organized output structure

#### 🎙️ **Speech Recognition** (`transcribe_vocals.py`)
Generates timestamped transcripts from isolated vocals using advanced Whisper models.

**Key Features:**
- Multiple Whisper model sizes
- Word-level timestamp accuracy
- CPU-compatible processing
- Configurable model parameters

#### 🔍 **Lyrics Search** (`search_lyrics.py`)
Searches Japanese lyrics database (uta-net.com) using intelligent web scraping.

**Key Features:**
- Dual search strategy (title → artist)
- Polite scraping with rate limiting
- Proper encoding handling
- Fallback mechanisms

#### ✅ **Quality Verification** (`verify_lyrics.py`)
Uses LLM analysis to verify downloaded lyrics match ASR transcript content.

**Key Features:**
- Content similarity analysis
- Confidence scoring system
- Detailed reasoning explanations
- Quality gate enforcement

#### 📝 **LRC Generation** (`generate_lrc.py`)
Creates synchronized LRC files by aligning lyrics with ASR timestamps.

**Key Features:**
- Intelligent timing alignment
- Grammar correction capabilities
- Multiple input format support
- LRC format validation

#### 🌐 **Translation** (`translate_lrc.py`)
Translates LRC files to Traditional Chinese while preserving synchronization.

**Key Features:**
- Bilingual LRC format creation
- Timing preservation
- Cultural adaptation
- Translation quality validation

### Utility Modules

#### 🔧 **Utilities** (`utils.py`)
Shared utility functions for file operations, path management, and data processing.

**Key Features:**
- File system operations
- Path management and organization
- Data format conversion
- Environment validation

#### 📋 **Logging Configuration** (`logging_config.py`)
Centralized logging system with colored output and flexible configuration.

**Key Features:**
- Colored console output
- File logging support
- Consistent formatting
- Terminal compatibility

#### 🎮 **Main Interface** (`main.py`)
Command-line interface and module coordination for testing and development.

**Key Features:**
- Action routing and dispatch
- Module testing interface
- Error handling and reporting
- Development workflow support

#### ⚡ **Batch Processor** (`process_lyrics.py`)
Comprehensive batch processing orchestrator for large music libraries.

**Key Features:**
- Recursive file discovery
- Progress tracking and reporting
- Resume functionality
- CSV result export

## 🔧 API Reference

### Module Interfaces

#### Metadata Extraction
```python
extract_metadata(file_path: str) -> dict
# Returns: {'title': str, 'artist': str, 'album': str, 'genre': str, 'year': str, 'track_number': str}
```

#### Song Identification
```python
identify_song_from_asr_with_retry(transcript: str, max_retries: int = 3) -> tuple
# Returns: (song_title, artist_name, native_language) or None
```

#### Lyrics Search
```python
search_uta_net(song_title: str, artist_name: str) -> str
# Returns: lyrics text or None
```

#### Lyrics Verification
```python
verify_lyrics_match(lyrics_text: str, asr_transcript: str) -> tuple
# Returns: (is_match: bool, confidence: float, reasoning: str)
```

#### Vocal Separation
```python
separate_vocals(input_file_path: str, output_dir: str = "output") -> str
# Returns: path to vocals file or None
```

#### Speech Recognition
```python
transcribe_with_timestamps(audio_file_path: str, model_size: str = "large-v3") -> list
# Returns: list of transcript segments with timestamps
```

#### LRC Generation
```python
generate_lrc_lyrics(client, lyrics_text: str, asr_transcript: str, model: str) -> str
# Returns: LRC formatted lyrics
```

#### Translation
```python
translate_lrc_content(client, lrc_content: str, target_language: str = "Traditional Chinese") -> str
# Returns: translated bilingual LRC content
```

## 🛠️ Development

### Project Structure
```
music-lyric/
├── docs/                    # Documentation
│   ├── README.md           # This file
│   ├── modules/            # Module documentation
│   └── guides/             # Development guides
├── prompt/                 # LLM prompt templates
├── tests/                  # Test suite
├── input/                  # Source audio files
├── output/                 # Final LRC files
├── tmp/                    # Processing temporary files
├── .kilocode/              # AI development configuration
└── *.py                    # Source modules
```

### Development Setup

1. **Environment Setup**
   ```bash
   uv sync --dev
   # Install development dependencies
   ```

2. **Code Quality**
   ```bash
   # Run tests
   uv run python -m pytest tests/

   # Check code formatting
   uv run python -m black --check .

   # Type checking (if mypy configured)
   uv run python -m mypy .
   ```

3. **Testing Individual Modules**
   ```bash
   # Test metadata extraction
   uv run python main.py metadata --file test.flac

   # Test lyrics search
   uv run python main.py search --file test.flac
   ```

### Adding New Features

1. **New Module Development**
   - Follow existing module patterns
   - Add comprehensive documentation in `docs/modules/`
   - Include proper error handling and logging
   - Add tests in `tests/` directory

2. **Pipeline Integration**
   - Update `process_lyrics.py` for new stages
   - Add configuration options as needed
   - Update documentation and examples

## 🐛 Troubleshooting

### Common Issues

#### Installation Problems
- **Issue**: `uv sync` fails
- **Solution**: Check Python version, ensure UV is installed correctly

#### API Configuration Issues
- **Issue**: "API key not found" errors
- **Solution**: Verify `.env` file configuration, check API key validity

#### Processing Failures
- **Issue**: Files fail to process
- **Solution**: Check logs for detailed error messages, verify file formats

#### Memory Issues
- **Issue**: Out of memory during processing
- **Solution**: Process files individually, use smaller models, increase system RAM

### Getting Help

1. **Check Documentation**: Review relevant module documentation in `docs/`
2. **Examine Logs**: Check log files for detailed error information
3. **Test Individual Components**: Use `main.py` to test specific modules
4. **Review Configuration**: Verify environment variables and settings

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
uv run python process_lyrics.py --log-level DEBUG
```

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone <your-fork-url>
   cd music-lyric
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

3. **Make Changes**
   - Follow existing code patterns
   - Add tests for new functionality
   - Update documentation

4. **Test Changes**
   ```bash
   uv run python -m pytest tests/
   uv run python main.py <action> --file test.flac
   ```

5. **Submit Pull Request**
   - Provide clear description of changes
   - Include test results and examples
   - Update documentation as needed

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Include comprehensive docstrings
- Add tests for new functionality
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **audio-separator** - AI-powered vocal separation
- **faster-whisper** - High-performance speech recognition
- **mutagen** - Audio metadata extraction
- **uta-net.com** - Japanese lyrics database
- **OpenAI** - LLM API and models

---

**Happy Lyrics Processing! 🎵**

For more information, see the [module documentation](modules/) or [development guides](guides/).