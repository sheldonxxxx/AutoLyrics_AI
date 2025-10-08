# Context: Music Lyrics Processing Pipeline

## Current State

Mature Python-based system for processing music files to generate synchronized LRC format lyrics with translation. Well-structured modular architecture supporting both individual components and full pipeline processing.

## Active Development Focus

Processing music files with lyrics from uta-net.com. Pipeline combines AI technologies for vocal separation, ASR transcription, and LLM-based alignment.

## Recent Changes

- Comprehensive batch processing script (`process_lyrics.py`)
- OpenAI API integration for LRC generation and translation
- Bilingual LRC support (original + Traditional Chinese)
- Separated UVR/ASR into distinct modules for better modularity
- Song-specific folder structure in `tmp/{relative_path}/{filename}/`
- Enhanced song identification with retry mechanism
- Centralized documentation architecture

## Next Steps

- Expand lyric sources beyond uta-net.com
- Optimize performance for large music libraries
- Add more translation languages
- Improve LRC synchronization accuracy