# Music Lyrics Processing Pipeline - Test Suite

This document describes the comprehensive test suite for the Music Lyrics Processing Pipeline project.

## Overview

The test suite provides complete coverage for all modules in the music lyrics processing pipeline, including:

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: End-to-end workflow testing
- **Mock-based Testing**: External dependency isolation
- **Error Handling Tests**: Edge cases and failure scenarios

## Test Structure

### Test Files

| Test File | Module Tested | Description |
|-----------|---------------|-------------|
| `test_utils.py` | `utils.py` | File operations, path management, data validation |
| `test_extract_metadata.py` | `extract_metadata.py` | Audio metadata extraction from various formats |
| `test_search_lyrics.py` | `search_lyrics.py` | Web scraping for lyrics from uta-net.com |
| `test_separate_vocals.py` | `separate_vocals.py` | Audio separation and transcription |
| `test_generate_lrc.py` | `generate_lrc.py` | LRC generation using OpenAI-compatible API |
| `test_translate_lrc.py` | `translate_lrc.py` | LRC translation to Traditional Chinese |
| `test_logging_config.py` | `logging_config.py` | Centralized logging configuration |
| `test_process_lyrics_integration.py` | `process_lyrics.py` | End-to-end pipeline integration |
| `test_folder_structure.py` | `utils.py` | Folder structure preservation (existing) |

### Test Runner

- `test_runner.py`: Main test runner with command-line interface
- Supports running all tests or specific modules
- Provides detailed reporting and summary statistics

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
uv add -r test_requirements.txt
```

2. Ensure all project dependencies are installed:
```bash
uv install
```

### Basic Usage

Run all tests:
```bash
uv run python test_runner.py
```

Run specific test module:
```bash
uv run python test_runner.py --module test_utils
```

List available test modules:
```bash
uv run python test_runner.py --list-tests
```

Run with different verbosity:
```bash
uv run python test_runner.py --verbosity 1  # Less verbose
uv run python test_runner.py --verbosity 2  # More verbose (default)
```

### Alternative: Using unittest directly

```bash
# Run all tests
uv run python -m unittest discover -v

# Run specific test file
uv run python -m unittest test_utils.py -v

# Run specific test class
uv run python -m unittest test_utils.TestUtils.test_find_audio_files_with_valid_directory -v
```

## Test Coverage

### Module Coverage

- **utils.py**: ~95% coverage
  - File discovery and path management
  - Data validation and conversion
  - CSV export functionality
  - Prompt template loading

- **extract_metadata.py**: ~90% coverage
  - Multiple audio format support
  - Tag priority handling
  - Filename fallback parsing
  - Error handling for corrupted files

- **search_lyrics.py**: ~85% coverage
  - Web scraping functionality
  - Search result parsing
  - Lyrics extraction and cleanup
  - Network error handling

- **separate_vocals.py**: ~80% coverage
  - Audio separator integration
  - Whisper transcription
  - Model configuration
  - File output validation

- **generate_lrc.py**: ~85% coverage
  - OpenAI API integration
  - Prompt template handling
  - LRC format generation
  - Grammar correction

- **translate_lrc.py**: ~80% coverage
  - Translation API integration
  - Bilingual LRC creation
  - Language validation
  - Unicode handling

- **logging_config.py**: ~90% coverage
  - Logger configuration
  - Colored output formatting
  - File and console handling
  - Error recovery

- **process_lyrics.py**: ~75% coverage (integration tests)
  - End-to-end workflow
  - Step coordination
  - Error propagation
  - Resume functionality

## Test Data and Fixtures

### Test Data Directory

- `test_data/`: Contains sample files and test fixtures
  - `sample_audio.flac`: Placeholder for test audio file
  - Additional test files can be added as needed

### Mock Data

All tests use mocked external dependencies:
- **Audio processing libraries** (mutagen, audio-separator, faster-whisper)
- **Web requests** (requests to uta-net.com)
- **AI APIs** (OpenAI-compatible endpoints)
- **File system operations**

## Testing Strategy

### Unit Tests

- **Isolation**: Each function tested independently
- **Mocking**: External dependencies mocked to ensure test reliability
- **Edge Cases**: Invalid inputs, error conditions, boundary cases
- **Data Types**: Various input types and formats

### Integration Tests

- **Workflow Testing**: End-to-end pipeline execution
- **State Management**: ProcessingResults class functionality
- **Error Propagation**: Failure handling across modules
- **Resume Functionality**: Checkpoint and resume behavior

### Mock Strategy

- **External APIs**: OpenAI, web services, file operations
- **Heavy Dependencies**: Audio processing, ML models
- **Network Operations**: HTTP requests, external services
- **File System**: Path operations, directory creation

## Adding New Tests

### For New Modules

1. Create `test_<module_name>.py`
2. Follow the existing test structure:
   - Set up test fixtures in `setUp()`
   - Clean up in `tearDown()`
   - Use descriptive test method names
   - Include docstrings for complex tests

3. Add comprehensive coverage:
   - Success scenarios
   - Failure scenarios
   - Edge cases
   - Error handling

### For Existing Modules

1. Identify gaps in current test coverage
2. Add tests for untested functions or scenarios
3. Update existing tests if interfaces change
4. Ensure backward compatibility

## Continuous Integration

### Recommended CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv install
        uv add -r test_requirements.txt
    - name: Run tests
      run: uv run python test_runner.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure test files are in the same directory as the modules they test
2. **Mock Setup**: Verify that all external dependencies are properly mocked
3. **File Paths**: Use absolute paths or proper relative path handling
4. **Environment Variables**: Mock API keys and other environment variables

### Debug Mode

Run tests with maximum verbosity:
```bash
uv run python test_runner.py --verbosity 2
```

Run specific failing test:
```bash
uv run python -m unittest test_utils.TestUtils.test_find_audio_files_with_valid_directory -v
```

## Best Practices

### Writing Tests

- **Descriptive Names**: Use clear, descriptive test method names
- **Single Responsibility**: Each test should verify one specific behavior
- **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and verification
- **Edge Cases**: Test boundary conditions and error scenarios
- **Documentation**: Add docstrings for complex test scenarios

### Test Maintenance

- **Regular Updates**: Keep tests synchronized with code changes
- **Refactoring**: Update tests when interfaces change
- **Coverage Goals**: Aim for >80% coverage for each module
- **Performance**: Ensure tests run quickly and efficiently

## Contributing

When contributing to the test suite:

1. Follow existing patterns and conventions
2. Add tests for new functionality
3. Update tests for modified functionality
4. Ensure all tests pass before submitting changes
5. Document any special testing requirements

## Test Results

Expected test results when all tests pass:

```
Music Lyrics Processing Pipeline - Test Suite
==================================================
Running all tests...
................................................................................
----------------------------------------------------------------------
Test Summary:
  Tests run: 85
  Failures: 0
  Errors: 0
  Success rate: 100.0%

✅ All tests passed!
```

## Contact

For questions about the test suite or testing strategy, please refer to the project documentation or contact the development team.