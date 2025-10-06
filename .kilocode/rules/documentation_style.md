# Documentation Style Guidelines

## General Documentation Principles

### Documentation Architecture
The Music Lyrics Processing Pipeline uses a **centralized documentation architecture** optimized for AI maintenance:

### Documentation Types
- **Module docstrings**: Minimal reference-style docstrings in code files
- **Centralized documentation**: Comprehensive markdown files in `docs/modules/`
- **Function docstrings**: Required for all public functions
- **Class docstrings**: Required for all classes
- **Inline comments**: Use sparingly for complex logic only
- **README files**: Keep project overview current and comprehensive

### Documentation Structure
```
docs/
├── README.md (main project documentation)
├── modules/ (individual module documentation)
│   ├── module_name.md (comprehensive module docs)
│   └── ...
└── guides/ (development and troubleshooting guides)
```

### Code Documentation Approach
- **Reference-Style Docstrings**: Clean, minimal docstrings (~50 lines)
- **External Documentation**: Comprehensive docs in `docs/modules/`
- **Cross-References**: Links between code and detailed documentation
- **AI-Optimized**: Efficient for automated maintenance

### Documentation Language
- Use clear, professional English
- Write in imperative mood ("Extract", not "Extracts")
- Be concise but comprehensive
- Use complete sentences with proper punctuation

### Reference-Style Docstrings
For code files, use minimal reference-style docstrings that point to external documentation:

```python
#!/usr/bin/env python3
"""
Extract song metadata from audio files.

This module handles metadata extraction for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/extract_metadata.md

Key Features:
- Multiple audio format support (FLAC, MP3, M4A, etc.)
- Intelligent tag priority system
- Filename fallback for missing metadata
- Comprehensive error handling

Dependencies:
- mutagen>=1.47.0
- logging_config (pipeline logging)

Pipeline Stage: 1/6 (Metadata Extraction)
"""
```

### External Documentation
Comprehensive documentation is maintained in `docs/modules/` markdown files:

```markdown
# Module Name

## Overview
Complete module overview with architecture and functionality.

## Pipeline Integration
How the module fits into the overall pipeline.

## Technical Implementation
Detailed technical implementation and dependencies.

## Usage Examples
CLI, programmatic, and pipeline integration examples.

## API Reference
Complete function and class documentation.

## Troubleshooting
Common issues and solutions.
```

## Module Documentation

### File Headers
- Start every Python file with a module docstring
- Include purpose, main functionality, and key features
- Mention dependencies and requirements

```python
#!/usr/bin/env python3
"""
Script to extract song name and artist name from audio file metadata.

This module provides functionality to read metadata from various audio
formats including FLAC, MP3, and other common formats. It handles
different tag formats and provides fallback mechanisms for files
without proper metadata tags.
"""
```

## Function Documentation

### Docstring Format
- Use triple quotes for all docstrings
- First line: Brief, imperative description
- Second line: Blank
- Subsequent lines: Detailed explanation
- Args section: List all parameters with types and descriptions
- Returns section: Describe return value with type information
- Raises section: Document expected exceptions

```python
def extract_metadata(file_path: str) -> dict:
    """
    Extract song metadata from audio file.

    Processes various audio formats and extracts available metadata
    including title, artist, album, and other tag information.
    Handles different tag formats and provides fallback to filename
    parsing when metadata is unavailable.

    Args:
        file_path (str): Path to the audio file to process

    Returns:
        dict: Dictionary containing extracted metadata with keys:
            - title: Song title
            - artist: Artist name
            - album: Album name
            - genre: Music genre
            - year: Release year
            - track_number: Track number

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be accessed
    """
    pass
```

### Parameter Documentation
- Document all parameters in the Args section
- Include type information in parentheses
- Provide meaningful descriptions
- Mention default values when applicable

## Class Documentation

### Class Docstrings
- Describe the class purpose and main functionality
- Mention key methods and their purposes
- Document initialization parameters
- Explain class-level behavior

```python
class AudioProcessor:
    """
    Main class for processing audio files in the lyrics pipeline.

    This class orchestrates the entire audio processing workflow including
    metadata extraction, vocal separation, transcription, and LRC generation.
    It provides both individual component access and complete pipeline
    processing capabilities.

    Args:
        input_dir (str): Directory containing audio files to process
        output_dir (str): Directory for processed output files

    Attributes:
        input_dir (str): Input directory path
        output_dir (str): Output directory path
        processed_files (List[str]): List of successfully processed files
    """
    pass
```

## Comment Guidelines

### When to Use Comments
- Complex business logic that isn't obvious from the code
- Workarounds for known issues or limitations
- TODO items for future improvements
- Important algorithmic explanations

### Comment Style
- Use complete sentences with proper punctuation
- Start with capital letter, end with period
- Place comments above the code they explain
- Use single space after comment marker

```python
# Define priority order for processing tags to ensure
# higher priority tags are processed first
prioritized_tags = []
for key, value in tags.items():
    # Define priorities: 0 = highest priority, higher numbers = lower priority
    if key_lower in ['title', 'tracktitle']:
        priority = 10  # Title tags
    elif key_lower in ['artist', 'albumartist']:
        priority = 20  # Primary artist tags
```

### What Not to Comment
- Obvious code that can be understood from variable names
- Commented-out code (remove it instead)
- Version history or author information (use git for this)
- Basic language constructs

## README Documentation

### Project README Structure
- **Title**: Clear, descriptive project name
- **Description**: Brief overview of what the project does
- **Installation**: Step-by-step setup instructions
- **Usage**: Examples and common use cases
- **Configuration**: Environment variables and settings
- **API Reference**: For library projects
- **Contributing**: Guidelines for contributors
- **License**: Project license information

### README Content Guidelines
- Use clear, non-technical language where possible
- Include practical examples
- Keep instructions current with latest changes
- Use code blocks for commands and configuration
- Include troubleshooting section for common issues

## Logging Documentation

### Log Message Guidelines
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include relevant context in log messages
- Avoid sensitive information in logs
- Use structured logging for complex data

```python
# Good logging examples
logger.info(f"Processing file: {filename}")
logger.warning(f"File not found, skipping: {filename}")
logger.error(f"API request failed for {filename}: {error}")

# Avoid generic messages
logger.info("Processing...")  # Too vague
logger.error("Error occurred")  # Not helpful for debugging
```

## Code Examples in Documentation

### Example Guidelines
- Use realistic, practical examples
- Include expected output when relevant
- Show both simple and advanced usage patterns
- Update examples when APIs change

```python
"""
Example usage:

    >>> from extract_metadata import extract_metadata
    >>> metadata = extract_metadata('song.flac')
    >>> print(f"Title: {metadata['title']}")
    Title: Song Title
    >>> print(f"Artist: {metadata['artist']}")
    Artist: Artist Name
"""
```

## Documentation Maintenance

### Keeping Documentation Current
- Update docstrings when function signatures change
- Review documentation during code reviews
- Update README for new features or breaking changes
- Remove outdated examples and instructions

### Documentation Standards
- Consistent formatting across all files
- Regular review and updates
- Clear separation between user-facing and internal documentation
- Appropriate level of detail for the audience

### Documentation Workflow for AI Maintenance
1. **Code Editing**: Work with clean, focused files
2. **Documentation Reference**: Access comprehensive docs when needed
3. **Consistency Maintenance**: Keep minimal docstrings in sync with detailed docs
4. **Cross-Reference Updates**: Update links between code and documentation
5. **Quality Assurance**: Regular review of documentation accuracy