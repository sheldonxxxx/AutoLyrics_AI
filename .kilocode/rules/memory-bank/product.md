# Product: Music Lyrics Processing Pipeline

## Overview

Python-based solution for processing music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities.

## Core Purpose

Automates creation of accurate, time-synchronized lyrics for music files by combining AI technologies to extract vocals, transcribe speech, and align lyrics with audio timing.

## Key Problems Solved

- **Manual Lyric Timing**: Eliminates need for manual synchronization
- **Lyric Availability**: Automatically searches and retrieves lyrics from online sources
- **Audio Processing**: Separates vocals from music for better transcription
- **Multi-language Support**: Provides translation capabilities
- **Batch Processing**: Handles multiple files recursively

## How It Works

Six-stage pipeline:
1. **Metadata Extraction**: Extract song info from audio files
2. **Lyrics Search**: Find lyrics on uta-net.com
3. **Vocal Separation**: AI-powered vocal isolation
4. **Transcription**: Generate timestamped text using Whisper ASR
5. **LRC Generation**: Create synchronized lyrics with timing
6. **Translation**: Convert to Traditional Chinese

## Target Users

- Music content creators
- Karaoke application developers
- Music player developers
- Accessibility tool creators
- Music enthusiasts
- International listeners

## Value

All-in-one solution for creating professional-quality synchronized lyrics from audio files using multiple AI technologies.