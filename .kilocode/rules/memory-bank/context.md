# Context: Music Lyrics Processing Pipeline

## Current State

The Music Lyrics Processing Pipeline is a mature Python-based system that successfully processes music files to extract lyrics, separate vocals, and generate synchronized LRC format lyrics with translation capabilities. The project is well-structured with a modular architecture that allows for both individual component execution and full pipeline processing.

## Active Development Focus

The system is currently focused on processing Japanese music files, with lyrics sourced from uta-net.com. The pipeline effectively combines AI technologies for vocal separation, ASR transcription, and LLM-based alignment to create time-synchronized lyrics.

## Recent Changes

- Implementation of a comprehensive batch processing script (`process_lyrics.py`) that orchestrates the entire workflow
- Integration with OpenAI-compatible APIs for LRC generation and translation
- Support for bilingual LRC files (original + Traditional Chinese translation)
- Checkpoint-based processing to skip completed steps when possible
- **Separated UVR and ASR functionality** into distinct modules (`separate_vocals.py` and `transcribe_vocals.py`) for better modularity
- **Implemented song-specific folder structure** - all intermediate files for each song are now organized in `tmp/{relative_path}/{filename}/` folders
- Enhanced vocal separation with custom output path support and automatic cleanup of instrumental files

## Next Steps

- Potential expansion to support additional lyric sources beyond uta-net.com
- Performance optimization for processing large music libraries
- Possible addition of more translation languages beyond Traditional Chinese
- Enhancement of the LRC synchronization accuracy through improved AI prompting