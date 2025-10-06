# Metadata Extraction Module

## 🎵 Audio Metadata Extraction (`extract_metadata.py`)

Extracts song metadata (title, artist, album, genre, year, track number) from various audio file formats. This is the first step in the Music Lyrics Processing Pipeline, providing essential information needed for subsequent steps like lyrics searching and LRC generation.

## Pipeline Integration

```
Input Audio Files    ┌──────────────────┐    Lyrics Search
(FLAC/MP3/etc) ───▶ │  extract_metadata │ ───▶ (next step)
                    │  (this module)   │
                    └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Extract song information from audio file metadata tags
- Provide fallback filename parsing when tags are missing
- Return standardized metadata dictionary for pipeline use

### Key Features
- **Multi-Format Support**: FLAC, MP3, M4A, OGG, and other mutagen-supported formats
- **Intelligent Tag Priority**: Sophisticated system for handling conflicting metadata
- **Filename Fallback**: Extracts artist/title from filename patterns when no tags exist
- **Comprehensive Error Handling**: Graceful handling of corrupted files and missing data

## Technical Implementation

### Dependencies
- **mutagen>=1.47.0**: Core library for audio metadata extraction
- **logging_config**: Consistent logging across pipeline
- **pathlib**: Cross-platform path handling

### Supported Audio Formats
- ✅ **FLAC files (.flac)** - Primary target format, lossless compression
- ✅ **MP3 files (.mp3)** - ID3v1/ID3v2 tags, most common format
- ✅ **M4A files (.m4a)** - MP4 metadata, Apple Lossless format
- ✅ **OGG Vorbis (.ogg)** - Vorbis comments, open source format
- ✅ **Other formats** - Any format supported by mutagen library

### Tag Priority System

The module uses a sophisticated priority system to handle conflicting or duplicate metadata tags:

| Priority | Tag Types | Description |
|----------|-----------|-------------|
| **10 (Highest)** | `title`, `tracktitle`, `©nam`, `tit2`, `tit3` | Song title information |
| **20** | `artist`, `albumartist`, `tpe1`, `tpe2`, `©art`, `aart`, `tp1`, `tp2` | Primary artist names |
| **30** | `composer`, `band`, `ensemble`, `tpe3`, `tpe4`, `tcom`, `text` | Secondary artist info |
| **40** | `album`, `©alb`, `talb` | Album information |
| **50** | `genre`, `©gen`, `tcon`, `gnre` | Music genre classification |
| **60** | `date`, `year`, `©day`, `tdrc`, `tyer` | Release year/date |
| **70** | `tracknumber`, `track`, `©trk`, `trck` | Track position/number |
| **80 (Lowest)** | All other tags | Miscellaneous metadata |

### Filename Fallback Strategy

When no metadata tags are available, the module attempts to extract information from the filename using common naming patterns:

**Pattern Recognition:**
- `"Artist - Title.flac"` → Artist: "Artist", Title: "Title"
- `"Album/Artist - Title.flac"` → Preserves directory structure context
- `"Title.flac"` → Title: "Title", Artist: None (null)

**Supported Patterns:**
- Standard "Artist - Title" format
- Album subdirectory organization
- Simple filename-only fallback

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Verify file exists and is accessible
2. **Format Detection**: Determine audio format (FLAC vs others)
3. **Metadata Extraction**: Use mutagen library to read audio tags
4. **Tag Prioritization**: Process tags in priority order
5. **Fallback Strategy**: Use filename parsing if no metadata exists
6. **Output Formatting**: Return standardized metadata dictionary

### Metadata Dictionary Format
```python
{
    'title': str | None,        # Song title
    'artist': str | None,       # Artist name
    'album': str | None,        # Album name
    'genre': str | None,        # Music genre
    'year': str | None,         # Release year
    'track_number': str | None  # Track number/position
}
```

## Error Handling & Edge Cases

### File Access Issues
- **FileNotFoundError**: File doesn't exist or path is invalid
- **PermissionError**: Insufficient permissions to read file
- **IsADirectoryError**: Path points to directory, not file

### Format-Specific Issues
- **FLACNoHeaderError**: Corrupted FLAC file or not a FLAC file
- **ID3NoHeaderError**: Corrupted MP3 file or not an MP3 file

### Metadata Issues
- **Empty tags**: Returns None for missing fields
- **Malformed tags**: Attempts to clean and validate data
- **Multiple values**: Takes first non-empty value from lists
- **Character encoding**: UTF-8 encoding issues in metadata

## Performance Considerations

### Optimization Features
- **Efficient Processing**: Early returns for complete metadata
- **Minimal I/O**: Reads metadata only (no audio decoding)
- **Memory Efficient**: Processes one file at a time
- **Fast Path**: Optimized for files with complete metadata

### Performance Characteristics
- **Processing Speed**: Typically milliseconds per file
- **Memory Usage**: Minimal (metadata only)
- **Scalability**: Efficient for large music libraries
- **I/O Impact**: Read-only operations, very low overhead

## Usage Examples

### Standalone CLI Usage
```bash
# Extract metadata from FLAC file
python extract_metadata.py path/to/audio.flac

# With custom logging level
python extract_metadata.py path/to/audio.flac --log-level DEBUG
```

### Programmatic Usage
```python
from extract_metadata import extract_metadata

# Extract metadata from audio file
metadata = extract_metadata("song.flac")

# Use extracted information
if metadata['title'] and metadata['artist']:
    print(f"Now processing: {metadata['title']} by {metadata['artist']}")
    # Continue with lyrics search or other operations
else:
    print("Missing title or artist, cannot proceed with lyrics search")
```

### Pipeline Integration
```python
# Used by process_lyrics.py as first processing step
metadata = extract_metadata(input_file)

# Metadata passed to subsequent pipeline stages
if metadata['title'] and metadata['artist']:
    lyrics = search_lyrics(metadata['title'], metadata['artist'])
```

## API Reference

### Functions

#### `extract_metadata(file_path: str) -> dict`
Extract song metadata from audio file.

**Parameters:**
- `file_path` (str): Path to the audio file to process

**Returns:**
- `dict`: Dictionary containing extracted metadata with keys: title, artist, album, genre, year, track_number

**Raises:**
- `FileNotFoundError`: If the specified file does not exist
- `PermissionError`: If the file cannot be accessed
- `FLACNoHeaderError`: If FLAC file is corrupted or invalid
- `ID3NoHeaderError`: If MP3 file is corrupted or invalid

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed tag processing information and priority assignments
- **INFO**: Successful metadata extraction results and summary
- **WARNING**: Missing metadata, fallback usage, or format issues
- **ERROR**: Critical failures preventing metadata extraction

### Example Log Output
```
INFO - Metadata extracted: Song Title - Artist Name
WARNING - No ID3 header found in file.mp3, trying FLAC parser
ERROR - Failed to extract metadata from corrupted.flac: FLACNoHeaderError
DEBUG - Processing tag 'TIT2' with priority 10 (title)
```

## Testing & Validation

### Test Coverage
- Various audio formats (FLAC, MP3, M4A, OGG)
- Different metadata configurations (complete, partial, missing)
- Filename fallback scenarios
- Error conditions and edge cases
- International character support

### Validation Checklist
- [ ] Proper metadata extraction from tagged files
- [ ] Correct filename fallback behavior
- [ ] Appropriate error handling for corrupted files
- [ ] International character encoding support
- [ ] Consistent output format across file types

## Common Pitfalls & Solutions

### Issue: "No metadata found for file"
**Symptoms:** Function returns all None values
**Causes:**
- File has no metadata tags
- Unsupported file format
- Corrupted or invalid file
**Solutions:**
- Check if file has proper metadata tags
- Verify file format is supported
- Test with known good files

### Issue: "FLACNoHeaderError"
**Symptoms:** Exception when processing FLAC files
**Causes:**
- File is not actually a FLAC file
- FLAC file is corrupted or truncated
- File header is damaged
**Solutions:**
- Verify file is valid FLAC format
- Check for corruption with media tools
- Try re-encoding if file is damaged

### Issue: "Permission denied"
**Symptoms:** Cannot access audio file
**Causes:**
- Insufficient file read permissions
- File is open in another application
- Network drive access issues
**Solutions:**
- Check file permissions with `ls -l`
- Close other applications using the file
- Verify network drive connectivity

### Issue: "Special characters not displaying correctly"
**Symptoms:** Garbled text in artist/title names
**Causes:**
- Character encoding issues in metadata
- Terminal/console encoding mismatch
- Font support for international characters
**Solutions:**
- Verify UTF-8 encoding in metadata
- Check terminal/console encoding settings
- Ensure font supports required character sets

## Maintenance & Development

### Adding New Formats
1. Check mutagen library support for the format
2. Add format detection logic if needed
3. Update supported formats documentation
4. Add tests for the new format

### Updating Tag Priorities
1. Research standard tag names for the format
2. Determine appropriate priority levels
3. Update priority assignment logic
4. Test with sample files

### Performance Optimization
- Monitor processing speed for large libraries
- Consider caching for frequently accessed files
- Optimize tag processing order if needed
- Profile memory usage patterns

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known good file
python extract_metadata.py known_good.flac

# Enable debug logging
python extract_metadata.py problem_file.flac --log-level DEBUG

# Check file information
file problem_file.flac
ls -l problem_file.flac
```

### Common Solutions
1. **Verify file format**: Use `file` command or media info tools
2. **Check file integrity**: Look for corruption or truncation
3. **Test permissions**: Ensure read access to file and directory
4. **Validate metadata**: Use media taggers to inspect tags manually

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Pipeline Architecture](../../README.md#architecture) - System architecture
- [Search Lyrics Module](search_lyrics.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions