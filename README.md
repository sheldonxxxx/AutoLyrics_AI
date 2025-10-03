# Music Lyrics Processing Pipeline

This project provides a comprehensive pipeline for processing music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities.

## Features

- **Metadata Extraction**: Extract song title, artist, and other metadata from audio files
- **Lyrics Search**: Search for lyrics on uta-net.com using song title and artist
- **Vocal Separation**: Separate vocals from music using audio-separator
- **Transcription**: Generate timestamped transcription of vocals using Whisper
- **LRC Generation**: Combine lyrics and transcription to create synchronized LRC files
- **Translation**: Translate LRC lyrics to Traditional Chinese (or other languages)

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
├── search_lyrics.py        # Search for lyrics online
├── separate_vocals.py      # Separate vocals and transcribe
├── generate_lrc.py         # Generate LRC format lyrics
├── translate_lrc.py        # Translate LRC lyrics
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

1. **Missing Dependencies**: Ensure all dependencies are installed via uv with `uv sync`
2. **API Key Issues**: Verify your API keys are correctly set in the `.env` file
3. **File Not Found**: Ensure input files exist in the correct directory
4. **Model Issues**: Some models may need to be downloaded automatically on first use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## New Script: Process All FLAC Files

The project now includes a new script `process_flac_lyrics.py` that orchestrates the entire workflow for processing all FLAC files in a directory (recursive).

### Features

- **Recursive Processing**: Finds and processes all FLAC files in a directory and its subdirectories
- **Complete Workflow**: Performs UVR vocal separation → ASR transcription → lyrics search → LRC generation → translation
- **Temporary Files**: Stores intermediate files in a temporary directory, only final LRC files go to output
- **Progress Tracking**: Shows progress when processing multiple files

### Usage

```bash
uv run process_flac_lyrics.py [input_directory] [options]
```

**Options:**
- `[input_directory]`: Input directory containing FLAC files (default: input)
- `--output-dir`, `-o`: Output directory for final LRC files (default: output)
- `--temp-dir`, `-t`: Temporary directory for intermediate files (default: tmp)
- `--skip-existing`: Skip files that already have output files
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

**Example:**
```bash
uv run process_flac_lyrics.py input/ --output-dir output/ --temp-dir tmp/ --skip-existing
```

### Output Structure

- **Temporary files** (in `tmp/` by default):
  - Separated vocals: `filename_(Vocals)_UVR_MDXNET_Main.wav`
  - ASR transcript: `filename_(Vocals)_UVR_MDXNET_Main_transcript.txt`
 - Downloaded lyrics: `filename_lyrics.txt`
  - Original LRC: `filename.lrc`

- **Final output** (in `output/` by default):
  - Translated LRC: `filename.lrc` (in Traditional Chinese)
