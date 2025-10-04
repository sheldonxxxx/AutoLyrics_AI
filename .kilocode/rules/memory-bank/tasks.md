# Tasks: Music Lyrics Processing Pipeline

## Adding New Translation Languages
**Last performed:** Initialization
**Files to modify:**
- `translate_lrc.py` - Update target language parameter
- `process_lyrics.py` - Update language in batch processing
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

## Implementing Lyrics Verification Workflow
**Last performed:** 2025-10-04
**Files to modify:**
- `verify_lyrics.py` - Create or modify verification function
- `prompt/lyrics_verification_prompt.txt` - Update verification prompt
- `identify_song.py` - Add retry mechanism with feedback
- `process_lyrics.py` - Integrate verification step
- Memory bank files - Update documentation

**Steps:**
1. Create `verify_lyrics.py` module with LLM-based verification function
2. Design prompt template for lyrics vs ASR content comparison
3. Modify `identify_song.py` to support retry mechanism with feedback
4. Update `process_lyrics.py` to integrate verification before LRC generation
5. Set confidence threshold (≥60%) for verification pass
6. Test integration and update memory bank documentation

**Important notes:**
- Verification prevents incorrect lyrics from proceeding to LRC generation
- Retry mechanism helps avoid wrong song identifications
- Maintain structured output format for verification results
- Update confidence thresholds based on testing results
