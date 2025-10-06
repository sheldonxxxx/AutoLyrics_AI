# Music Lyrics Processing Pipeline

## Overview
Python-based pipeline that processes music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities.

## Core Features
- **Metadata Extraction**: Extract song info from audio files
- **Lyrics Search**: Find lyrics on uta-net.com using song metadata
- **Vocal Separation**: AI-powered vocal isolation from music tracks
- **ASR Transcription**: Generate timestamped text from vocals
- **LRC Generation**: Create synchronized lyrics with timing
- **Translation**: Convert lyrics to Traditional Chinese
- **Batch Processing**: Process entire music libraries automatically

## Technology Stack
- Python 3.13+
- audio-separator (vocal separation)
- faster-whisper (speech recognition)
- OpenAI API (LRC generation/translation)
- BeautifulSoup4 (web scraping)
- Mutagen (metadata extraction)

## Value
Automates creation of synchronized lyrics for music files, combining AI technologies for vocal extraction, speech transcription, and lyric alignment.