# Metadata Extraction Module

## 🎵 Audio Metadata Extraction (`extract_metadata.py`)

Extracts song metadata (title, artist, album, genre, year, track number) from various audio file formats. This is the first step in the Music Lyrics Processing Pipeline, providing essential information needed for subsequent steps like lyrics searching and LRC generation.

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