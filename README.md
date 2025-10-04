# Music Lyrics Processing Pipeline

🎵 **AI-Powered Lyrics Processing** → 🎤 **Vocal Separation** → 🔍 **Smart Verification** → 📝 **Synchronized LRC**

This project provides a comprehensive pipeline for processing music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities.

## 🚀 Project Summary

| **Input** | **Process** | **Output** |
|-----------|-------------|------------|
| Audio files (FLAC/MP3) | AI separates vocals → transcribes → finds lyrics → **verifies accuracy** → syncs timestamps | Bilingual LRC files (Original + Traditional Chinese) |

**Key Innovation**: LLM-powered verification ensures only matching lyrics proceed to LRC generation, with retry logic for song identification.

## Features

- **Metadata Extraction**: Extract song title, artist, and other metadata from audio files
- **Song Identification**: Identify songs from ASR transcripts using LLM and web search (with retry)
- **Lyrics Search**: Search for lyrics on uta-net.com using song title and artist
- **Lyrics Verification**: Verify downloaded lyrics match ASR content using LLM (prevents incorrect lyrics)
- **Vocal Separation**: Separate vocals from music using audio-separator
- **Transcription**: Generate timestamped transcription of vocals using Whisper
- **LRC Generation**: Combine verified lyrics and transcription to create synchronized LRC files
- **Translation**: Translate LRC lyrics to Traditional Chinese (or other languages)

## Pipeline Workflow

```
🎵 Input Audio Files
         │
         ▼
┌─────────────────────────────────────────────────┐
│  🎵 EXTRACT METADATA                            │
│  • Read audio tags (title, artist, album)       │
│  • Fallback to filename parsing if needed       │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  🎤 SEPARATE VOCALS & TRANSCRIBE                │
│  • Use UVR to isolate vocals from music         │
│  • Generate timestamped ASR transcription       │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  🔍 IDENTIFY SONG (if no metadata)              │
│  • Use LLM + web search on ASR transcript       │
│  • Retry up to 3 times with feedback            │
│  • Cache results for future use                 │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  📝 SEARCH LYRICS                               │
│  • Query uta-net.com using title + artist       │
│  • Download and parse lyrics text              │
│  • Handle Japanese characters properly          │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  ✅ VERIFY LYRICS MATCH ASR                     │
│  • **NEW: LLM compares lyrics vs transcript**    │
│  • Requires ≥60% confidence for match           │
│  • Prevents wrong lyrics from proceeding        │
└─────────────────────────────────────────────────┘
         │ (if verification passes)
         ▼
┌─────────────────────────────────────────────────┐
│  🎼 GENERATE LRC FILE                           │
│  • Combine verified lyrics + ASR timestamps     │
│  • Create synchronized [mm:ss.xx] format        │
│  • Ensure proper timing alignment               │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  🌏 TRANSLATE TO TRADITIONAL CHINESE           │
│  • Convert lyrics while preserving timestamps   │
│  • Create bilingual LRC file                    │
│  • Maintain original + translated text          │
└─────────────────────────────────────────────────┘
         │
         ▼
🎯 OUTPUT: Synchronized Bilingual LRC Files
```

### Workflow Details

1. **🎵 Input Processing**: Audio files (FLAC/MP3) are processed recursively from input directory
2. **📋 Metadata Extraction**: Song title, artist, and other metadata extracted from audio tags
3. **🎤 Separate Vocals & Transcribe**: Use UVR to isolate vocals, generate timestamped ASR transcription
4. **🔍 Song Identification**: If metadata missing, LLM identifies song from ASR transcript (up to 3 retries)
5. **📝 Lyrics Search**: Downloads lyrics from uta-net.com using title + artist
6. **✅ Quality Verification**: **NEW: LLM verifies lyrics match ASR content (≥60% confidence required)**
7. **🎼 LRC Generation**: Creates synchronized LRC file combining verified lyrics + ASR timestamps
8. **🌏 Translation**: Translates LRC to Traditional Chinese while preserving timestamps

### Quality Assurance Features

- ✅ **Retry Logic**: Song identification retries up to 3 times with feedback
- ✅ **Verification Gate**: Only verified lyrics (≥60% confidence) proceed to LRC generation
- ✅ **Error Handling**: Graceful degradation if any step fails
- ✅ **Progress Tracking**: Detailed logging and CSV output for batch processing

## Quick Start Guide

### 🎯 One-Command Setup
```bash
# 1. Clone and setup
git clone <repository-url>
cd music-lyric
uv sync

# 2. Configure API (create .env file)
echo "OPENAI_API_KEY=your_key_here" > .env
echo "OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1" >> .env

# 3. Process your music files
uv run process_lyrics.py input/ --resume
```

### 📋 What Happens
1. **Auto-detects** all audio files in `input/` folder
2. **Extracts** song metadata (title, artist) from audio tags
3. **Identifies** songs from vocals if metadata missing (AI-powered)
4. **Downloads** lyrics from uta-net.com
5. **Verifies** lyrics match actual song content (prevents wrong lyrics)
6. **Creates** synchronized LRC files with timestamps
7. **Translates** to Traditional Chinese

### 🎵 Input/Output Example
```
input/
├── artist1/
│   ├── song1.flac
│   └── song2.mp3
└── artist2/
    └── album/
        └── song3.flac

# After processing:
output/
├── artist1/
│   ├── song1.lrc  # Synchronized lyrics (Original + Traditional Chinese)
│   └── song2.lrc
└── artist2/
    └── album/
        └── song3.lrc
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd music-lyric
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment variables by creating a `.env` file:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1
OPENAI_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507
```

## Usage

### Quick Start

Run the main pipeline with default settings:
```bash
uv run main.py
```

### Individual Components

The pipeline can be run in parts using the main script:

```bash
# Extract metadata from an audio file
uv run main.py metadata --file input/your_song.flac

# Search for lyrics online
uv run main.py search --file input/your_song.flac

# Separate vocals and transcribe
uv run main.py separate --file input/your_song.flac

# Generate LRC lyrics from transcript
uv run main.py generate --file input/your_song.flac

# Translate LRC lyrics to Traditional Chinese
uv run main.py translate --file input/your_song.flac
```

### Individual Scripts

Each component can also be run directly:

```bash
# Extract metadata
uv run extract_metadata.py input/your_song.flac

# Debug metadata
uv run debug_metadata.py input/your_song.flac

# Search for lyrics
uv run search_lyrics.py input/your_song.flac

# Separate vocals
uv run separate_vocals.py input/your_song.flac

# Generate LRC lyrics
uv run generate_lrc.py

# Translate LRC lyrics
uv run translate_lrc.py input/your_song.lrc
```

## Configuration

### Logging

All scripts support configurable logging levels:
```bash
uv run extract_metadata.py input/your_song.flac --log-level DEBUG
```

### Output Directories

- Input files should be placed in the `input/` directory
- Output files are saved in the `output/` directory
- Models are stored in the `models/` directory

## Project Structure

```
music-lyric/
├── input/                  # Input audio files
├── output/                 # Output lyrics, transcripts, and LRC files
├── models/                 # Audio separation and transcription models
├── logging_config.py       # Centralized logging configuration
├── extract_metadata.py     # Extract metadata from audio files
├── identify_song.py        # Identify songs from ASR transcripts (with retry)
├── search_lyrics.py        # Search for lyrics online
├── verify_lyrics.py        # NEW: Verify lyrics match ASR content
├── separate_vocals.py      # Separate vocals from music
├── transcribe_vocals.py    # Generate timestamped transcriptions
├── generate_lrc.py         # Generate LRC format lyrics
├── translate_lrc.py        # Translate LRC lyrics
├── process_lyrics.py       # NEW: Orchestrate full workflow with verification
├── debug_metadata.py       # Debug script for metadata
├── main.py                 # Main entry point
└── README.md               # This file
```

## Requirements

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for package management
- Required Python packages (see `pyproject.toml`)
- Audio files in common formats (FLAC, MP3, etc.)
- API key for OpenAI-compatible service for LRC generation and translation

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all dependencies are installed via uv with `uv sync`
2. **API Key Issues**: Verify your API keys are correctly set in the `.env` file
3. **File Not Found**: Ensure input files exist in the correct directory
4. **Model Issues**: Some models may need to be downloaded automatically on first use

### New Features Troubleshooting

**Lyrics Verification Failed**
- **Problem**: Lyrics don't match ASR content (confidence <60%)
- **Solution**: Check if the downloaded lyrics are for the correct song, or if the ASR transcription has quality issues
- **Tip**: The system will retry song identification up to 3 times if verification fails

**Song Identification Issues**
- **Problem**: Cannot identify song from ASR transcript
- **Solution**: Ensure ASR transcript has sufficient content (at least a few sentences of lyrics)
- **Tip**: Check the transcript file in `tmp/` folder to see ASR quality

**Low Confidence Results**
- **Problem**: System returns low confidence matches
- **Solution**: This is normal for poor quality audio or very obscure songs
- **Tip**: Consider using higher quality audio files or checking if songs exist on uta-net.com

### Getting Help

- Check the `tmp/` folder for intermediate files (transcripts, lyrics) to debug issues
- Use `--log-level DEBUG` for detailed logging information
- All processing steps are logged with timestamps for troubleshooting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Enhanced Pipeline: Process Lyrics with Verification

The project now includes an enhanced script `process_lyrics.py` that orchestrates the complete workflow with quality assurance features for processing all audio files in a directory (recursive).

### Features

- **Recursive Processing**: Finds and processes all audio files in a directory and its subdirectories
- **Complete Workflow**: Performs metadata extraction → song identification → lyrics search → **LLM verification** → LRC generation → translation
- **Quality Assurance**: **NEW: Verifies downloaded lyrics match ASR content using LLM** (prevents incorrect lyrics)
- **Retry Mechanism**: **NEW: Up to 3 attempts for song identification with feedback**
- **Temporary Files**: Stores intermediate files in a temporary directory, only final LRC files go to output
- **Progress Tracking**: Shows progress when processing multiple files

### Usage

```bash
uv run process_lyrics.py [input_directory] [options]
```

**Options:**
- `[input_directory]`: Input directory containing audio files (default: input)
- `--output-dir`, `-o`: Output directory for final LRC files (default: output)
- `--temp-dir`, `-t`: Temporary directory for intermediate files (default: tmp)
- `--resume`: Resume processing by skipping files that already have output files
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

**Example:**
```bash
uv run process_lyrics.py input/ --output-dir output/ --temp-dir tmp/ --resume
```

### Workflow with Verification

1. **Extract Metadata** → Extract song title, artist from audio files
2. **Identify Song** → If no metadata, identify from ASR transcript (with retry)
3. **Search Lyrics** → Download lyrics from uta-net.com
4. **Verify Match** → **NEW: LLM compares lyrics with ASR content**
5. **Generate LRC** → Only if verification passes (≥60% confidence)
6. **Translate LRC** → Convert to Traditional Chinese

### Output Structure

- **Temporary files** (in `tmp/` by default):
  - Separated vocals: `filename_(Vocals)_UVR_MDXNET_Main.wav`
  - ASR transcript: `filename_(Vocals)_UVR_MDXNET_Main_transcript.txt`
  - Downloaded lyrics: `filename_lyrics.txt`
  - Song identification: `filename_song_identification.json`
  - Original LRC: `filename.lrc`

- **Final output** (in `output/` by default):
  - Translated LRC: `filename.lrc` (in Traditional Chinese)
