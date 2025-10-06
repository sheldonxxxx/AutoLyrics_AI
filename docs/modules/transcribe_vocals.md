# Vocal Transcription Module

## 🎙️ ASR Transcription (`transcribe_vocals.py`)

Handles the critical speech recognition step of converting separated vocals into timestamped text transcripts. This module utilizes the faster-whisper library with advanced Whisper models to provide high-accuracy transcription with word-level timing information essential for LRC file generation.

## Pipeline Integration

```
Vocal Audio        ┌──────────────────┐    LRC Generation
(isolated)   ───▶ │  transcribe_     │ ───▶ (next step)
                  │  vocals.py       │
                  └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Convert isolated vocals to timestamped text transcripts
- Provide precise timing information for LRC generation
- Support multiple Whisper model sizes for different accuracy needs
- Enable both standalone usage and pipeline integration

### Key Features
- **Multiple Model Sizes**: From tiny (~39MB) to large-v3 (~1550MB)
- **Word-Level Timestamps**: Precise timing for individual words
- **CPU Compatible**: Works without GPU acceleration
- **Configurable Parameters**: Adjustable accuracy vs. speed trade-offs
- **Robust Error Handling**: Graceful handling of audio issues

## Technical Implementation

### Dependencies
- **faster-whisper>=1.2.0**: Optimized Whisper implementation for speed
- **logging_config**: Consistent logging across pipeline
- **pathlib**: Cross-platform path handling

### Whisper Model Architecture

#### Model Size Options
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| **tiny** | ~39 MB | Fastest | Lower | Quick testing, low-resource |
| **base** | ~74 MB | Fast | Good | General purpose, balanced |
| **small** | ~244 MB | Moderate | Better | Improved accuracy needed |
| **medium** | ~769 MB | Slower | Higher | High accuracy requirements |
| **large-v1** | ~1550 MB | Slow | High | Best accuracy, English-focused |
| **large-v2** | ~1550 MB | Slow | Very High | Multi-language, improved |
| **large-v3** | ~1550 MB | Slow | Best | Latest, most accurate (default) |
| **large-v3-turbo** | ~809 MB | Faster | Slightly Less | Speed-optimized version |

#### Compute Type Optimization
Optimizes processing for different hardware capabilities:

- **int8**: 8-bit quantization, fastest, minimal quality loss
- **int8_float32**: Mixed precision, good balance of speed/accuracy
- **int16**: 16-bit quantization, higher quality, slower processing
- **float16**: Half precision, requires GPU, fastest on compatible hardware
- **float32**: Full precision, highest quality, slowest processing

### Timestamp Accuracy Levels

#### Segment Level
- Complete phrases or sentences
- Start/end times for logical text units
- Basic timing for LRC generation

#### Word Level (Default)
- Individual word timing within segments
- Precise positioning for karaoke-style lyrics
- Enhanced synchronization accuracy

#### Character Level (Advanced)
- Precise character positioning within words
- Maximum timing precision for professional applications
- Requires compatible model versions

### Example Output Format
```
[0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
[4.46s -> 8.12s] 地球は回る 君の心に太陽が
[8.12s -> 12.34s] 沈まないように 僕がずっと
[12.34s -> 15.67s] 君の側にいるから
```

### Supported Audio Formats
- ✅ **WAV files (.wav)** - Uncompressed PCM, preferred for transcription
- ✅ **FLAC files (.flac)** - Lossless compression
- ✅ **MP3 files (.mp3)** - Lossy compression (may affect accuracy)
- ✅ **M4A files (.m4a)** - AAC compression
- ✅ **Other formats** - Any format supported by faster-whisper

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Verify vocal audio file exists and is accessible
2. **Model Selection**: Load specified Whisper model size and configuration
3. **Audio Preprocessing**: Prepare audio for optimal transcription
4. **Speech Recognition**: Apply Whisper model for text extraction
5. **Timestamp Extraction**: Capture word-level timing information
6. **Segment Processing**: Organize results into structured format
7. **Output Formatting**: Return segments with start/end times and text

### Processing Parameters

#### Configurable Settings
- **beam_size**: Search beam size (default: 5, higher = more accurate)
- **word_timestamps**: Enable word-level timing (default: True)
- **language**: Auto-detection or forced language setting
- **temperature**: Sampling temperature for diversity (default: 0)
- **compression_ratio_threshold**: Filter for repetitive text
- **no_repeat_ngram_size**: Prevent repetitive n-grams

#### Model Configuration
```python
# High accuracy configuration
transcribe_with_timestamps(
    audio_file_path="vocals.wav",
    model_size="large-v3",
    device="cpu",
    compute_type="float32"
)

# Fast processing configuration
transcribe_with_timestamps(
    audio_file_path="vocals.wav",
    model_size="base",
    device="cpu",
    compute_type="int8"
)
```

## Error Handling & Edge Cases

### Audio Quality Issues
- **Poor quality vocals**: Issues from separation process affecting recognition
- **Background noise**: Artifacts or residual music in isolated vocals
- **Low volume**: Very quiet or distorted audio
- **Accented speech**: Heavily accented or non-standard pronunciation

### Model Limitations
- **Size vs. accuracy trade-offs**: Larger models are slower but more accurate
- **Language-specific performance**: Better performance on trained languages
- **Musical content**: Singing vs. speaking recognition challenges
- **Hardware constraints**: Processing time vs. available resources

### Content Challenges
- **Non-Japanese lyrics**: Model may struggle with other languages
- **Artistic vocalizations**: Non-standard pronunciation or effects
- **Tempo variations**: Very fast or slow singing tempos
- **Vocal harmonies**: Overlapping vocals or background singers

### Technical Issues
- **Memory limitations**: Large models requiring significant RAM
- **Processing timeouts**: Very long files exceeding time limits
- **Hardware acceleration**: GPU unavailable for acceleration
- **Model download failures**: Network or storage issues

## Performance Considerations

### Processing Characteristics
- **Model Loading**: 10-60 seconds depending on size
- **Processing Speed**: 5-20x real-time (CPU processing)
- **Memory Usage**: 2-8GB depending on model size
- **Disk Usage**: Temporary model storage (~500MB-2GB)

### Performance Factors
**Processing time varies by:**
- **Model size**: Larger models = slower but more accurate
- **Audio length**: Linear relationship with file duration
- **Hardware specifications**: CPU cores and speed affect performance
- **Audio quality**: Complex or noisy audio requires more processing

### Optimization Strategies
- **Model Selection**: Choose appropriate size for use case
- **Batch Processing**: Process multiple files efficiently
- **Resource Management**: Monitor memory usage for large models
- **Quality vs. Speed**: Balance accuracy needs with processing time

## Usage Examples

### Standalone CLI Usage
```bash
# Basic transcription with default settings
python transcribe_vocals.py vocals.wav

# High accuracy transcription
python transcribe_vocals.py vocals.wav --model large-v3

# Fast processing for testing
python transcribe_vocals.py vocals.wav --model base --compute-type int8

# Debug mode with detailed logging
python transcribe_vocals.py vocals.wav --log-level DEBUG
```

### Programmatic Usage
```python
from transcribe_vocals import transcribe_with_timestamps

# Basic transcription
segments = transcribe_with_timestamps("vocals.wav")
print(f"Generated {len(segments)} transcript segments")

# Custom model configuration
segments = transcribe_with_timestamps(
    audio_file_path="vocals.wav",
    model_size="large-v3",
    device="cpu",
    compute_type="int8"
)

# Process segments
for segment in segments:
    start_time = segment.start
    end_time = segment.end
    text = segment.text
    print(f"[{start_time:.2f}s -> {end_time:.2f}s] {text}")
```

### Pipeline Integration
```python
# Used by process_lyrics.py as third processing step
from transcribe_vocals import transcribe_with_timestamps

# Transcribe vocals with timestamps
segments = transcribe_with_timestamps(vocals_file)

if segments:
    # Save transcript for LRC generation
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write("Timestamped Transcription:\n\n")
        for segment in segments:
            f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")

    # Continue with lyrics search and LRC generation
    lyrics_content = search_lyrics(metadata['title'], metadata['artist'])
else:
    # Handle transcription failure
    logger.error("Transcription failed, cannot generate LRC")
```

## API Reference

### Functions

#### `transcribe_with_timestamps()`
Main function for audio transcription with timestamps.

**Parameters:**
- `audio_file_path` (str): Path to audio file to transcribe
- `model_size` (str): Whisper model size (default: "large-v3")
- `device` (str): Processing device (default: "cpu")
- `compute_type` (str): Computation precision (default: "int8")

**Returns:**
- `list`: List of segment objects with start, end, and text attributes

**Raises:**
- `ImportError`: If faster-whisper is not installed
- `FileNotFoundError`: If audio file does not exist
- `RuntimeError`: If transcription fails due to audio issues

## Output Verification

### Successful Transcription Criteria
- **Reasonable segments**: Typically 20-100 segments for a song
- **Proper timing**: Start < end, chronological order
- **Meaningful content**: Actual lyrics, not noise or silence
- **Language detection**: Appropriate language for content

### Quality Assessment
- **Accuracy**: Text should match audio content
- **Completeness**: All major lyrics should be captured
- **Timing precision**: Word boundaries should align with audio
- **Consistency**: Similar segments should have similar formatting

## Logging & Debugging

### Log Levels
- **DEBUG**: Model loading and detailed processing information
- **INFO**: Successful transcription and segment counts
- **WARNING**: Quality issues or fallback behaviors
- **ERROR**: Critical failures preventing transcription

### Example Log Output
```
INFO - Loading Whisper model: large-v3 on cpu
INFO - Transcribing: song_(Vocals)_UVR_MDXNET_Main.wav
INFO - Transcription completed: 45 segments, 8.2 minutes audio
DEBUG - [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
WARNING - Low confidence transcription for segment, manual review recommended
ERROR - Transcription failed: Model loading timeout
```

## Testing & Validation

### Test Coverage
- Various vocal qualities and audio formats
- Different music genres and vocal styles
- Multiple model sizes and configurations
- Edge cases (very short/long files, poor quality audio)
- Hardware variations (different CPU speeds and memory)

### Validation Checklist
- [ ] Transcription produces readable, accurate text
- [ ] Timestamps align correctly with audio content
- [ ] Model selection works across different use cases
- [ ] Error handling works for problematic audio files
- [ ] Performance meets expectations for target hardware

## Common Pitfalls & Solutions

### Issue: "Model loading failed"
**Symptoms:** Model fails to load during initialization
**Causes:**
- Insufficient disk space for model storage
- Network issues preventing model download
- Corrupted model files
**Solutions:**
- Check available disk space in model directory
- Verify internet connection for downloads
- Try smaller model size if space is limited

### Issue: "Poor transcription accuracy"
**Symptoms:** Generated text doesn't match audio content
**Causes:**
- Poor quality vocals from separation
- Inappropriate model for language/content
- Audio format or encoding issues
**Solutions:**
- Try larger model for better accuracy
- Check vocal separation quality first
- Consider language-specific model tuning

### Issue: "Out of memory during processing"
**Symptoms:** Processing fails with memory errors
**Causes:**
- Model too large for available RAM
- Very long audio files
- Memory leaks or inefficient processing
**Solutions:**
- Use smaller model size (base instead of large)
- Process shorter files if possible
- Increase system RAM or close other applications

### Issue: "Processing timeout"
**Symptoms:** Transcription takes extremely long or hangs
**Causes:**
- Very long audio files
- Underpowered hardware
- Model loading or initialization issues
**Solutions:**
- Check system resources (CPU, RAM, disk)
- Consider splitting very long files
- Monitor for hardware bottlenecks

## Maintenance & Development

### Model Management
- **Updates**: Monitor faster-whisper for model improvements
- **Versions**: Keep track of model version compatibility
- **Storage**: Manage local model storage and cleanup
- **Selection**: Update default model based on performance testing

### Performance Optimization
- **Hardware**: Consider GPU acceleration for faster processing
- **Batch Processing**: Optimize for multiple file processing
- **Caching**: Implement model caching for repeated use
- **Configuration**: Fine-tune parameters for specific use cases

### Adding New Models
1. **Research**: Identify suitable models for transcription
2. **Testing**: Validate performance across audio types
3. **Integration**: Add model selection logic to module
4. **Documentation**: Update documentation with new options

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known good audio
python transcribe_vocals.py known_good_vocals.wav

# Check model loading
python transcribe_vocals.py test.wav --log-level DEBUG

# Monitor system resources
htop  # or similar system monitor during processing
```

### Common Solutions
1. **Verify audio format**: Use supported formats (WAV, FLAC, MP3, M4A)
2. **Check audio quality**: Poor vocals affect transcription accuracy
3. **Test model sizes**: Start with base model, upgrade if needed
4. **Monitor resources**: Ensure sufficient RAM for chosen model size

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Vocal Separation Module](separate_vocals.md) - Previous pipeline stage
- [LRC Generation Module](generate_lrc.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions