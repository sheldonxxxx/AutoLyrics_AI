# Music Lyrics Processing Pipeline

## Project Overview
This project provides a comprehensive pipeline for processing music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities.

## Main Objectives
- Extract song metadata from audio files
- Search for and retrieve lyrics from online sources
- Separate vocals from music tracks using AI
- Generate timestamped transcriptions of vocals
- Create synchronized LRC format lyrics
- Translate lyrics to different languages (Traditional Chinese)

## Key Features
- **Metadata Extraction**: Extract song title, artist, and other metadata from audio files
- **Song Identification**: Identify songs from ASR transcripts using LLM and web search (with retry)
- **Lyrics Search**: Search for lyrics on uta-net.com using song title and artist
- **Lyrics Verification**: NEW: Verify downloaded lyrics match ASR content using LLM
- **Vocal Separation**: Separate vocals from music using audio-separator
- **Transcription**: Generate timestamped transcription of vocals using Whisper
- **LRC Generation**: Combine verified lyrics and transcription to create synchronized LRC files
- **Translation**: Translate LRC lyrics to Traditional Chinese (or other languages)
- **Batch Processing**: Process all FLAC files in a directory recursively with quality assurance

## Technologies Used
- Python 3.13+
- audio-separator (for vocal separation)
- faster-whisper (for ASR transcription)
- OpenAI-compatible API (for LRC generation and translation)
- BeautifulSoup4 (for web scraping lyrics)
- Mutagen (for metadata extraction)
- Requests (for HTTP operations)
- uv (package manager)

## Significance
This project automates the complex process of creating synchronized lyrics for music files, which is valuable for music players, karaoke applications, and accessibility tools. It combines multiple AI technologies to extract vocals, transcribe speech, and align lyrics with audio timing, making it a powerful tool for music content creators and enthusiasts.