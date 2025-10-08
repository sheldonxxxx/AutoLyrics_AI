# Tasks: Music Lyrics Processing Pipeline

## Adding New Translation Languages
**Last performed:** Initialization
**Files to modify:**
- `translate_lrc.py` - Update target language parameter
- `process_lyrics.py` - Update language in batch processing

**Steps:**
1. Update the target language parameter in the translation function
2. Adjust the prompt in `translate_lrc.py` to support the new language
3. Test with sample LRC files to ensure proper translation

**Important notes:**
- Ensure the LLM supports the target language
- Maintain LRC format during translation
- Preserve timestamps and metadata lines

