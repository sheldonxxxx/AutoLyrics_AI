# Tasks: Music Lyrics Processing Pipeline

## Batch Processing Workflow
**Last performed:** Initialization
**Files involved:**
- `process_flac_lyrics.py` - Main batch processing orchestrator
- `utils.py` - File discovery and path management utilities
- Individual component scripts (extract_metadata.py, search_lyrics.py, etc.)

**Steps:**
1. Use `find_flac_files()` to recursively discover all FLAC files in input directory
2. For each file, generate output paths using `get_output_paths()`
3. Extract metadata using `extract_metadata()`
4. Separate vocals using `separate_vocals()` (UVR)
5. Transcribe vocals with timestamps using `transcribe_with_timestamps()` (Whisper)
6. Search for lyrics using `search_uta_net()` (web scraping)
7. Generate LRC using `generate_lrc_lyrics()` (LLM alignment)
8. Translate LRC to Traditional Chinese using `translate_lrc.py` (LLM translation)

**Important notes:**
- Checkpoint-based processing: Skip steps if output files already exist
- All temporary files stored in tmp/ directory
- Final bilingual LRC files saved to output/ directory
- Progress tracking for multiple files

## Adding New Translation Languages
**Last performed:** Initialization
**Files to modify:**
- `translate_lrc.py` - Update target language parameter
- `process_flac_lyrics.py` - Update language in batch processing
- Memory bank files if needed

**Steps:**
1. Update the target language parameter in the translation function
2. Adjust the prompt in `translate_lrc.py` to support the new language
3. Test with sample LRC files to ensure proper translation
4. Update documentation if needed

**Important notes:**
- Ensure the LLM supports the target language
- Maintain LRC format during translation
- Preserve timestamps and metadata lines