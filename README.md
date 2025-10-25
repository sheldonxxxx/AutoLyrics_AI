# Music Lyrics Processing Pipeline

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sheldonxxxx_AutoLyrics_AI&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=sheldonxxxx_AutoLyrics_AI)

🎵 **AI-Powered Lyrics Processing** → 🎤 **Vocal Separation** → 🔍 **Song Identification** → 📝 **Synchronized LRC**

Python-based pipeline that processes music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities. This mature system features a well-structured modular architecture supporting both individual components and full pipeline processing.

## 🚀 Project Summary

| **Input** | **Process** | **Output** |
|-----------|-------------|------------|
| Audio files | vocals separation  → transcribes → identifies songs → finds lyrics → syncs timestamps | Bilingual LRC files (Original + Target Language) |

## Features

- **Metadata Extraction**: Extract song title, artist, and other metadata from audio files
- **Song Identification**: Identify songs from ASR transcripts using AI Agent and web search mcp server
- **Vocal Separation**: Separate vocals from music using audio-separator
- **Transcription**: Generate timestamped transcription of vocals using Whisper
- **Lyrics Search**: Search for lyrics using AI Agent
- **LRC Generation**: Combine verified lyrics and transcription to create synchronized LRC files
- **Translation**: Translate LRC lyrics to desired language

### Workflow Details

1. **🎵 Input Processing**: Audio files (FLAC/MP3) are processed recursively from input directory
2. **📋 Metadata Extraction**: Song title, artist, and other metadata extracted from audio tags
3. **🎤 Separate Vocals & Transcribe**: Use UVR to isolate vocals, generate timestamped ASR transcription
4. **🔍 Identify Song & Search Lyrics**: If no metadata, use LLM to identify song; search for lyrics using web-search-mcp
5. **🎼 LRC Generation**: Creates synchronized LRC file combining lyrics + ASR timestamps
6. **🌏 Translation**: Translates LRC to target language while preserving timestamps
7. **🎯 Output**: Saves synchronized bilingual LRC files to output directory

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd music_lyric
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment variables by creating a `.env` file:
```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=

# MCP Server Configuration for web search (choose one option below)
# Option 1: Remote MCP server (recommended for production)
MCP_SEARXNG_SERVER_URL=http://your-server:3000/mcp

# Option 2: Local MCP server (requires npx installed)
# SEARXNG_URL=http://your-searxng-instance:8080

# Optional: Logfire observability (for advanced logging and monitoring)
LOGFIRE_WRITE_TOKEN=
```

## Usage

### Quick Start

Run the main pipeline with default settings:
```bash
uv run process_lyrics.py <path to input folder>
```

### Command Line Arguments

The `process_lyrics.py` script supports the following command line arguments:

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `input_dir` | - | Input directory containing audio files (FLAC or MP3) | `input` |
| `--output-dir` | `-o` | Output directory for final LRC files | `output` |
| `--temp-dir` | `-t` | Temporary directory for intermediate files | `tmp` |
| `--resume` | - | Resume processing by skipping files that already have output files | `False` |
| `--log-level` | - | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `--logfire` | - | Enable Logfire integration for advanced logging | `False` |
| `--csv-output` | `-c` | CSV file to save processing results | `results_YYYYMMDD_HHMMSS.csv` |
| `--no-color` | - | Disable colored logging output | `False` |
| `--target-language` | - | Target language for translation | `Traditional Chinese` |

#### Example Usage

```bash
# Basic usage with custom directories
uv run process_lyrics.py /path/to/music --output-dir /path/to/output --temp-dir /path/to/temp

# Resume interrupted processing with debug logging
uv run process_lyrics.py input --resume --log-level DEBUG

# Process with custom translation language and CSV output
uv run process_lyrics.py input --target-language Japanese --csv-output results.csv

# Full featured processing with all options
uv run process_lyrics.py input \
  --output-dir output \
  --temp-dir tmp \
  --resume \
  --log-level INFO \
  --csv-output processing_results.csv \
  --target-language "Traditional Chinese"
```

## Configuration

### Environment Variables

The following environment variables can be configured in your `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | API key for OpenAI-compatible service (e.g., DashScope) |
| `OPENAI_BASE_URL` | Yes | Base URL for the OpenAI-compatible API endpoint |
| `OPENAI_MODEL` | Yes | Model name for LRC generation and translation |
| `MCP_SEARXNG_SERVER_URL` | No* | Remote MCP server URL for web search (e.g., `http://server:3000/mcp`) |
| `SEARXNG_URL` | No* | SearXNG instance URL for local MCP server (fallback when remote MCP not available) |
| `LOGFIRE_WRITE_TOKEN` | No | Optional token for Logfire observability and advanced logging |

*Note: Either `MCP_SEARXNG_SERVER_URL` or `SEARXNG_URL` is required for song identification functionality.

### Remote MCP Server Setup (Optional)

#### Docker Compose (quickest setup)**
```yaml
services:
  mcp-searxng:
    image: ghcr.io/sheldonxxxx/mcp-searxng:latest
    container_name: mcp-searxng
    environment:
      - SEARXNG_URL=http://searxng:8080
      - MCP_HTTP_PORT=3000
    restart: unless-stopped
    ports:
      - 3000:3000
```

**For detailed setup instructions and configuration, see**: [https://github.com/sheldonxxxx/mcp-searxng.git](https://github.com/sheldonxxxx/mcp-searxng.git)

**List of public Searxng server: [https://searx.space](https://searx.space)**

### Logging

All scripts support configurable logging levels:
```bash
uv run extract_metadata.py input/your_song.flac --log-level DEBUG
```

#### Logfire Integration

For advanced observability and monitoring, you can enable Logfire integration:

1. Set the `LOGFIRE_WRITE_TOKEN` environment variable in your `.env` file
2. Use the `--logfire` flag when running `process_lyrics.py`:
```bash
uv run process_lyrics.py input --logfire
```

Logfire provides enhanced logging capabilities including structured logging, performance monitoring, and detailed error tracking for production deployments.

### Output Directories

- Input files should be placed in the `input/` directory
- Output files are saved in the `output/` directory
- Models are stored in the `models/` directory

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) for package management
- API key for OpenAI-compatible service for LRC generation and translation

### Tested Hardware & Models

This project has been tested and verified on:
- **M2 Pro MacBook** (16GB RAM)
- **Mac Mini M4** (16GB RAM)

**Tested LLM Model:**
- **Qwen-plus** (via DashScope API)

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