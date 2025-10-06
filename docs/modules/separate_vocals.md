# Vocal Separation Module

## 🌊 AI-Powered Vocal Separation (`separate_vocals.py`)

Handles the critical audio processing step of separating vocals from background music using AI-powered source separation. This module utilizes the audio-separator library with the UVR (Ultimate Vocal Remover) model to isolate human voices from full music tracks, enabling cleaner ASR transcription and better lyric alignment.

## Pipeline Integration

```
Full Audio         ┌──────────────────┐    ASR Transcription
(music+vocals) ───▶ │  separate_vocals │ ───▶ (next step)
                   │  (this module)   │
                   └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Isolate vocals from background music using AI
- Prepare clean audio for ASR transcription
- Organize output files in structured directories
- Automatic cleanup of non-essential audio files

### Key Features
- **AI-Powered Separation**: UVR model for high-quality vocal isolation
- **Multi-Format Support**: FLAC, MP3, WAV, M4A, and more
- **Organized Output**: Song-specific folder structure
- **Automatic Cleanup**: Removes instrumental files to save space
- **CPU Compatible**: Works without GPU acceleration

## Technical Implementation

### Dependencies
- **audio-separator[cpu]>=0.39.0**: Core library for AI-powered source separation
- **logging_config**: Consistent logging across pipeline
- **pathlib**: Cross-platform path handling

### Model Architecture

#### UVR-MDX-NET-Main Model
- **Specialization**: Optimized for vocal separation from music
- **Training**: Diverse music genres and vocal styles
- **Processing**: CPU-based for broad compatibility
- **Quality**: High-quality vocal isolation results

#### Model Characteristics
- **Size**: ~500MB download
- **Speed**: 1-5 minutes per typical song (CPU)
- **Memory**: 2-8GB RAM depending on file size
- **Output**: High-quality isolated vocals

### Supported Audio Formats
- ✅ **FLAC files (.flac)** - Lossless compression, preferred format
- ✅ **MP3 files (.mp3)** - Compressed, widely supported
- ✅ **WAV files (.wav)** - Uncompressed PCM format
- ✅ **M4A files (.m4a)** - Apple Lossless/ACC format
- ✅ **Other formats** - Any format supported by audio-separator

### Output File Naming Convention
Follows consistent, predictable naming pattern:
```
Input:  "song.flac"
Output: "song_(Vocals)_UVR_MDXNET_Main.wav"
Pattern: "{stem}_(Vocals)_UVR_MDXNET_Main.{ext}"
```

### Directory Structure Organization
Maintains organized file hierarchy for processing:

```
tmp/
└── {relative_path}/
    └── {filename}/
        ├── {filename}_(Vocals)_UVR_MDXNET_Main.wav      # ← Main output
        ├── {filename}_(Instrumental)_UVR_MDXNET_Main.wav # ← Auto-deleted
        ├── {filename}_(Drums)_UVR_MDXNET_Main.wav        # ← Auto-deleted
        └── {filename}_(Bass)_UVR_MDXNET_Main.wav         # ← Auto-deleted
```

### Cleanup Strategy
**Automatic Removal** (to save disk space):
- Instrumental tracks (music without vocals)
- Drum tracks (if separated)
- Bass tracks (if separated)
- Other non-vocal stems

**Preserved Files**:
- Vocals track (essential for transcription)
- Original input file (preserved for reference)

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Verify audio file exists and is accessible
2. **Model Setup**: Download and configure UVR model if needed
3. **Audio Loading**: Load audio file into processing pipeline
4. **Source Separation**: Apply AI model to separate vocal components
5. **Output Processing**: Identify and extract vocals-only audio
6. **File Management**: Move vocals to specified location
7. **Cleanup Process**: Remove instrumental and other non-vocal files

### Processing Parameters
**Configurable Settings:**
- **Model**: UVR_MDXNET_Main (default, optimized for vocals)
- **Output Format**: WAV (standard for further processing)
- **Processing Mode**: CPU (compatible, not fastest)
- **Single Stem**: Vocals only (focused output)

## Error Handling & Edge Cases

### File System Issues
- **Insufficient disk space**: Processing requires temporary storage
- **Permission denied**: Input/output directory access problems
- **Corrupted files**: Unreadable or malformed audio files

### Model-Related Issues
- **Model download failures**: Network or storage problems
- **Incompatible versions**: Model file corruption or version mismatch
- **GPU unavailable**: Falls back to CPU processing

### Audio Quality Issues
- **Extremely low quality**: Poor source audio affecting separation
- **No discernible vocals**: Instrumental or non-vocal content
- **Unusual formats**: Multi-track files with complex structures

### Processing Issues
- **Memory exhaustion**: Large files requiring too much RAM
- **Processing timeout**: Very long tracks exceeding time limits
- **Hardware limitations**: Slow CPU affecting processing speed

## Performance Considerations

### Processing Characteristics
- **Speed**: ~1-5 minutes per typical song (CPU processing)
- **Memory**: ~2-8GB RAM depending on file size and length
- **Disk Usage**: Temporary files during processing (~2x input size)
- **Network**: Initial model download (~500MB one-time)

### Performance Factors
**Processing time varies by:**
- **Audio length**: Linear relationship with file duration
- **Audio quality**: Complex music requires more processing
- **Hardware specs**: CPU speed and core count affect speed
- **Model version**: Different models have different performance

### Optimization Strategies
- **Batch Processing**: Process multiple files in sequence
- **Resource Management**: Monitor memory usage for large files
- **Cleanup Automation**: Automatic removal of temporary files
- **Progress Monitoring**: Real-time status for long operations

## Usage Examples

### Standalone CLI Usage
```bash
# Basic vocal separation
python separate_vocals.py path/to/audio.flac

# Custom output directory
python separate_vocals.py path/to/audio.flac --output-dir tmp

# Custom model selection
python separate_vocals.py path/to/audio.flac --model UVR_MDXNET_Main.onnx

# Debug mode
python separate_vocals.py path/to/audio.flac --log-level DEBUG
```

### Programmatic Usage
```python
from separate_vocals import separate_vocals

# Basic separation
vocals_path = separate_vocals("input/song.flac")
print(f"Vocals saved to: {vocals_path}")

# Custom output location
vocals_path = separate_vocals(
    "input/song.flac",
    output_dir="tmp",
    vocals_output_path="tmp/song/vocals.wav"
)

# Custom model
vocals_path = separate_vocals(
    "input/song.flac",
    model="UVR_MDXNET_Main.onnx"
)
```

### Pipeline Integration
```python
# Used by process_lyrics.py as second processing step
from separate_vocals import separate_vocals

# Separate vocals for transcription
vocals_file = separate_vocals(
    input_file,
    output_dir=temp_dir,
    vocals_output_path=paths['vocals_wav']
)

if vocals_file:
    # Continue with ASR transcription
    segments = transcribe_with_timestamps(vocals_file)
else:
    # Handle separation failure
    logger.error("Vocal separation failed")
```

## API Reference

### Functions

#### `separate_vocals()`
Main function for vocal separation using audio-separator.

**Parameters:**
- `input_file_path` (str): Path to input audio file
- `output_dir` (str): Directory for separated files (default: "output")
- `model` (str): Model filename for separation (default: "UVR_MDXNET_Main.onnx")
- `vocals_output_path` (str): Specific path for vocals output file (optional)

**Returns:**
- `str`: Path to vocals file if successful, None otherwise

**Raises:**
- `FileNotFoundError`: Input file does not exist
- `PermissionError`: Cannot access input/output directories

#### `_cleanup_non_vocals_files()`
Internal function for cleaning up non-vocal files.

**Parameters:**
- `output_files` (list): List of all output files from separation
- `output_dir` (str): Directory containing the files

## Output Verification

### Successful Separation Criteria
- **Valid WAV format**: Proper file structure and headers
- **Single channel**: Mono audio (vocals typically mono)
- **Standard sample rate**: 44.1kHz or 48kHz
- **Clear vocal content**: Audible vocals without music
- **Reasonable file size**: Typically 10-50% of original file size

### Quality Assessment
- **Audio clarity**: Vocals should be clear and intelligible
- **Music removal**: Background music should be minimized
- **Artifact reduction**: Minimal processing artifacts or noise
- **Consistency**: Quality should be consistent across file

## Logging & Debugging

### Log Levels
- **DEBUG**: Model loading and detailed processing information
- **INFO**: Successful separation and file operations
- **WARNING**: Fallback behaviors and minor issues
- **ERROR**: Critical failures preventing separation

### Example Log Output
```
INFO - Loading audio file: input/song.flac
INFO - Vocals extracted successfully: tmp/song/song_(Vocals)_UVR_MDXNET_Main.wav
INFO - Cleaned up 3 instrumental files, kept 1 vocals file
WARNING - Using CPU processing (GPU not available)
ERROR - Failed to separate vocals for corrupted.flac: Audio file corrupted
```

## Testing & Validation

### Test Coverage
- Various audio formats (FLAC, MP3, WAV, M4A)
- Different music genres and vocal styles
- Various audio qualities and bitrates
- Edge cases (very short/long files, corrupted files)
- Cleanup process verification

### Validation Checklist
- [ ] Vocal separation produces audible, clear vocals
- [ ] Instrumental files are properly cleaned up
- [ ] Output files have correct format and specifications
- [ ] Processing works across different audio qualities
- [ ] Error handling works for problematic files

## Common Pitfalls & Solutions

### Issue: "Model download failed"
**Symptoms:** Model download hangs or fails during first run
**Causes:**
- Network connectivity issues
- Insufficient disk space for model
- Firewall or proxy blocking downloads
**Solutions:**
- Check internet connection and firewall settings
- Verify available disk space in model directory
- Try manual download if automatic download fails

### Issue: "Out of memory during processing"
**Symptoms:** Processing fails with memory errors
**Causes:**
- File too large for available RAM
- Memory leaks in processing pipeline
- Other applications consuming memory
**Solutions:**
- Process smaller files individually
- Increase system RAM if possible
- Close other memory-intensive applications

### Issue: "Poor vocal quality"
**Symptoms:** Separated vocals have poor quality or artifacts
**Causes:**
- Poor quality source audio
- Inappropriate model for content type
- Processing parameters not optimized
**Solutions:**
- Check source audio quality first
- Try different model if available
- Verify audio format and bitrate

### Issue: "Processing timeout"
**Symptoms:** Processing takes extremely long or hangs
**Causes:**
- Very long audio files
- Underpowered hardware
- Model loading issues
**Solutions:**
- Check system resources (CPU, RAM)
- Consider splitting very long files
- Monitor for hardware issues

## Maintenance & Development

### Model Management
- **Updates**: Monitor audio-separator library for model improvements
- **Versions**: Keep track of model version compatibility
- **Storage**: Manage local model storage and cleanup
- **Alternatives**: Consider other models for different use cases

### Performance Optimization
- **Hardware**: Consider GPU acceleration for faster processing
- **Batch Size**: Optimize for available system resources
- **Caching**: Implement model caching for repeated use
- **Parallelization**: Explore concurrent processing options

### Adding New Models
1. **Research**: Identify suitable models for vocal separation
2. **Testing**: Validate performance across different audio types
3. **Integration**: Add model selection logic to module
4. **Documentation**: Update documentation with new model information

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known good file
python separate_vocals.py known_good.flac

# Check model directory
ls -la models/

# Monitor system resources during processing
htop  # or similar system monitor

# Enable debug logging
python separate_vocals.py file.flac --log-level DEBUG
```

### Common Solutions
1. **Verify file format**: Use `file` command or media tools
2. **Check file integrity**: Look for corruption with media scanners
3. **Monitor disk space**: Ensure sufficient space for processing
4. **Test with small files**: Isolate issues with file size/complexity

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Transcribe Vocals Module](transcribe_vocals.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions
- [Process Lyrics Module](process_lyrics.md) - Batch processing orchestrator