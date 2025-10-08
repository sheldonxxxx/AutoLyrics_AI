# Vocal Transcription Module

## 🎙️ ASR Transcription (`transcribe_vocals.py`)

Handles the critical speech recognition step of converting separated vocals into timestamped text transcripts. This module utilizes the faster-whisper library with advanced Whisper models to provide high-accuracy transcription with word-level timing information essential for LRC file generation.

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
