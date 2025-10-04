# Architecture: Music Lyrics Processing Pipeline

## System Architecture

The Music Lyrics Processing Pipeline follows a modular, component-based architecture where each stage of the processing pipeline is implemented as a separate module that can be run independently or as part of the full workflow.

### High-Level Architecture

```
Input FLAC Files
       ↓
[extract_metadata.py] → Extract song metadata (title, artist, etc.)
       ↓ (if no metadata)
[identify_song.py] → Identify song from ASR transcript (with retry)
       ↓
[search_lyrics.py] → Search for lyrics on uta-net.com
       ↓
[verify_lyrics.py] → NEW: Verify lyrics match ASR content using LLM
       ↓ (if verification passes)
[generate_lrc.py] → Combine verified lyrics and ASR transcript to create LRC
       ↓
[translate_lrc.py] → Translate LRC to Traditional Chinese
       ↓
Output: Synchronized LRC files in output directory
```

### Core Components

#### 1. `extract_metadata.py`
- **Purpose**: Extract song metadata from audio files
- **Technology**: Uses `mutagen` library for audio metadata extraction
- **Features**:
 - Supports multiple audio formats (FLAC, MP3, etc.)
  - Extracts title, artist, album, genre, year, track number
  - Handles various tag formats (ID3, FLAC, etc.)
  - Falls back to filename parsing if no tags exist

#### 2. `identify_song.py`
- **Purpose**: Identify song from ASR transcript using LLM and web search (with retry)
- **Technology**: Uses OpenAI-compatible API and SearXNG for song identification
- **Features**:
  - Performs web search using ASR transcript content
  - Uses LLM for intelligent song matching
  - **NEW: Retry mechanism with up to 3 attempts**
  - **NEW: Feedback system for improved identification**
  - Caching system for identified songs

#### 3. `search_lyrics.py`
- **Purpose**: Search for lyrics on uta-net.com using song title and artist
- **Technology**: Uses `requests` and `beautifulsoup4` for web scraping
- **Features**:
  - Performs title-based and artist-based searches
  - Extracts lyrics with proper formatting and line breaks
  - Handles rate limiting with delays between requests

#### 3. `separate_vocals.py`
- **Purpose**: Separate vocals from music using UVR
- **Technology**: Uses `audio-separator` for vocal separation
- **Features**:
  - Uses UVR (UVR_MDXNET_Main) model for vocal separation
  - Supports custom output paths for song-specific folder organization
  - CPU-based processing for compatibility
  - Automatic cleanup of instrumental files to save disk space

#### 3.1. `transcribe_vocals.py`
- **Purpose**: Transcribe vocals with timestamped transcription
- **Technology**: Uses `faster-whisper` for ASR transcription
- **Features**:
  - Generates timestamped transcription with word-level timestamps
  - CPU-based processing for compatibility
  - Standalone CLI interface for transcription-only operations

#### 4. `generate_lrc.py`
- **Purpose**: Generate LRC format lyrics by combining reference lyrics and ASR transcript
- **Technology**: Uses OpenAI-compatible API for alignment and formatting
- **Features**:
  - Combines reference lyrics with ASR timestamps
  - Maintains proper LRC format with [mm:ss.xx] timestamps
  - Uses LLM for intelligent alignment of lyrics to timestamps

#### 5. `translate_lrc.py`
- **Purpose**: Translate LRC lyrics to Traditional Chinese (bilingual output)
- **Technology**: Uses OpenAI-compatible API for translation
- **Features**:
  - Creates bilingual LRC files with original and translated lyrics
  - Preserves timestamps and LRC formatting
  - Maintains original metadata lines

#### 6. `verify_lyrics.py`
- **Purpose**: Verify downloaded lyrics match ASR transcript content using LLM
- **Technology**: Uses OpenAI-compatible API for content verification
- **Features**:
  - Compares lyrics with ASR transcript for content similarity
  - Returns confidence scores and detailed reasoning
  - Structured output with match verification
  - Prevents incorrect lyrics from proceeding to LRC generation

#### 7. `process_lyrics.py`
- **Purpose**: Orchestrates the full workflow for batch processing with verification
- **Features**:
  - Recursively processes all FLAC files in a directory
  - Manages temporary and output directories
  - Implements skip-existing functionality
  - Provides progress tracking
  - **NEW: Integrated lyrics verification workflow**
  - **NEW: Retry mechanism for song identification**

### Data Flow Architecture

#### File Path Management (`utils.py`)
- `find_flac_files()`: Recursively discovers FLAC files
- `get_output_paths()`: Maps input files to all intermediate/output paths
- `ensure_output_directory()`: Creates necessary directories

#### Output Directory Structure
```
tmp/ (temporary files)
└── {relative_path}/
    └── {filename}/ (song-specific folder)
        ├── {filename}_(Vocals)_UVR_MDXNET_Main.wav (separated vocals)
        ├── {filename}_(Vocals)_UVR_MDXNET_Main_transcript.txt (ASR transcript)
        ├── {filename}_lyrics.txt (downloaded lyrics)
        └── {filename}.lrc (generated LRC)
output/ (final files)
└── {relative_path}/
    └── {filename}.lrc (translated bilingual LRC)
```

### Technical Architecture

#### Configuration Management
- Environment variables for API configuration (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
- Support for custom base URLs for OpenAI-compatible services
- Logging configuration through centralized module

#### Logging Architecture (`logging_config.py`)
- Centralized logging configuration across all modules
- Consistent format and level management
- Support for both console and file logging
- UTF-8 encoding for international characters

#### Error Handling
- Comprehensive exception handling in each module
- Graceful degradation when components fail
- Detailed logging of errors and warnings
- Validation of inputs and outputs

### API Integration Architecture

The system uses OpenAI-compatible APIs for both LRC generation and translation:
- Custom base URL support for alternative providers
- Model selection through environment variables
- Structured prompting for consistent outputs
- Error handling for API failures

### Processing Pipeline Architecture

The system supports both component-level and full-pipeline processing:
- Individual scripts can be run standalone
- Main orchestrator (`main.py`) coordinates components
- Batch processor (`process_flac_lyrics.py`) handles multiple files
- Checkpoint-based processing (skips completed steps when possible)