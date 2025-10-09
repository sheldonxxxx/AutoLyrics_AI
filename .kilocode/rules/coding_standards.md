# Python Coding Standards

## General Style Guidelines

### Python Version and Type Hints
- Use Python 3.13+ features and syntax
- Always use type hints for function parameters and return values
- Import `typing` module for complex type annotations

```python
from typing import List, Dict, Optional, Tuple
from pathlib import Path

def process_files(input_files: List[Path]) -> Dict[str, str]:
    """Process multiple files and return results."""
    pass
```

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports within the project
- Group imports with blank lines between groups

```python
import os
from pathlib import Path
from typing import List

from mutagen import File
from openai import OpenAI

from logging_config import get_logger
```

## Naming Conventions

### Functions and Variables
- Use `snake_case` for function names and variables
- Use descriptive names that clearly indicate purpose
- Use constants in `UPPER_CASE` for configuration values

```python
def extract_metadata(file_path: str) -> dict:
    """Extract metadata from audio file."""
    MAX_RETRIES = 3
    file_extension = Path(file_path).suffix.lower()
    return metadata
```

### Classes
- Use `PascalCase` for class names
- Use `snake_case` for method names
- Private methods should start with single underscore

```python
class AudioProcessor:
    """Main class for processing audio files."""

    def __init__(self):
        self._internal_state = None

    def process_file(self, file_path: str) -> bool:
        """Process a single audio file."""
        pass

    def _validate_input(self, file_path: str) -> bool:
        """Validate input file path."""
        pass
```

## Code Structure

### Function Design
- Keep functions focused on single responsibility
- Use early returns to avoid deep nesting
- Limit function length to 50-60 lines when possible
- Use descriptive parameter names

```python
def find_audio_files(directory: str) -> List[Path]:
    """Find all audio files in directory recursively."""
    if not Path(directory).exists():
        logger.error(f"Directory does not exist: {directory}")
        return []

    audio_extensions = {'.flac', '.mp3', '.wav', '.m4a'}
    audio_files = []

    for file_path in Path(directory).rglob('*'):
        if file_path.suffix.lower() in audio_extensions:
            audio_files.append(file_path)

    return audio_files
```

### Error Handling
- Use specific exception types rather than generic Exception
- Log errors with appropriate levels (error, warning, info)
- Provide meaningful error messages
- Handle expected errors gracefully

```python
try:
    audio_file = File(file_path)
    metadata = extract_tags(audio_file)
except FLACNoHeaderError:
    logger.warning(f"No FLAC header found in {file_path}")
except ID3NoHeaderError:
    logger.warning(f"No ID3 header found in {file_path}")
except Exception as e:
    logger.error(f"Unexpected error processing {file_path}: {e}")
```

## Documentation

### Docstrings
- Use triple quotes for all docstrings
- Include Args, Returns, and Raises sections for public functions
- Use imperative mood ("Extract", not "Extracts")
- Keep first line concise, expand in following lines

```python
def extract_metadata(file_path: str) -> dict:
    """
    Extract song metadata from audio file.

    Processes various audio formats and extracts available metadata
    including title, artist, album, and other tag information.

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

### Comments
- Use comments to explain complex logic, not obvious code
- Use complete sentences with proper punctuation
- Comment before the code they explain
- Avoid commented-out code in production

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
    # ... rest of conditions
```

## Code Quality

### Readability
- Use meaningful variable names
- Break long lines at logical points (before operators)
- Use parentheses for line continuation
- Align related code blocks

### Constants and Configuration
- Define constants at module level
- Use environment variables for configuration
- Group related constants together

```python
# Audio processing constants
SUPPORTED_FORMATS = {'.flac', '.mp3', '.wav', '.m4a'}
DEFAULT_OUTPUT_DIR = 'output'
DEFAULT_TEMP_DIR = 'tmp'

# API configuration
DEFAULT_MODEL = 'Qwen/Qwen3-235B-A22B-Instruct-2507'
API_TIMEOUT = 30
MAX_RETRIES = 3
```

### Testing
- Write unit tests for all public functions
- Use descriptive test function names
- Test both success and failure scenarios
- Mock external dependencies in tests

## File Organization

### Module Structure
- Start each file with appropriate shebang and module docstring
- Organize functions logically within files
- Use `if __name__ == "__main__":` for CLI entry points
- Keep related functionality together

### CLI Interfaces
- Use `argparse` for command-line interfaces
- Provide helpful descriptions and examples
- Include logging level configuration
- Handle file paths appropriately

```python
def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Extract metadata from audio files'
    )
    parser.add_argument('input_file', help='Path to input audio file')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory path')

    args = parser.parse_args()
    # ... rest of main function
```

## Dependency Management

### Package Management with uv
- **Always use `uv add` for new dependencies** instead of manually editing `pyproject.toml`
- Use `uv remove` when removing dependencies to ensure proper cleanup
- Let uv handle dependency resolution and lock file management automatically

```bash
# ✅ Correct - Add new dependencies
uv add requests>=2.32.0

# ✅ Correct - Remove dependencies
uv remove unused-package

# ❌ Incorrect - Manual pyproject.toml editing
# Don't manually edit pyproject.toml for dependency changes
```

### Dependency Guidelines
- Pin major versions when stability is critical (e.g., `>=1.0.0,<2.0.0`)
- Use minimum version pins for flexibility (e.g., `>=2.32.0`)
- Group related dependencies in logical blocks in `pyproject.toml`
- Regularly update dependencies using `uv lock --upgrade`
- Test thoroughly after major dependency updates

### Virtual Environment Management
- Always use `uv run` to execute Python scripts instead of `python` or `python3`
- This ensures the correct virtual environment and dependencies are used
- Examples:
  ```bash
  uv run python script.py                    # Run a Python script
  uv run python -m py_compile file.py       # Compile Python files
  uv run python -c "import module"          # Test module imports
  ```

## Performance Considerations

### Efficient Processing
- Use appropriate data structures for the task
- Avoid unnecessary file I/O operations
- Process files in batches when possible
- Use logging instead of print statements for debugging

### Memory Management
- Process large files in chunks when possible
- Clean up temporary files after processing
- Use context managers for file operations
- Avoid loading entire files into memory unnecessarily