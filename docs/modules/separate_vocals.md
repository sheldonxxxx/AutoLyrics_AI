# Vocal Separation Module

## 🌊 AI-Powered Vocal Separation (`separate_vocals.py`)

Handles the critical audio processing step of separating vocals from background music using AI-powered source separation. This module utilizes the audio-separator library with the UVR (Ultimate Vocal Remover) model to isolate human voices from full music tracks, enabling cleaner ASR transcription and better lyric alignment.

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

### Supported Audio Formats
- ✅ **FLAC files (.flac)** - Lossless compression, preferred format
- ✅ **MP3 files (.mp3)** - Compressed, widely supported
- ✅ **WAV files (.wav)** - Uncompressed PCM format
- ✅ **M4A files (.m4a)** - Apple Lossless/ACC format
- ✅ **Other formats** - Any format supported by audio-separator

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Verify audio file exists and is accessible
2. **Model Setup**: Download and configure UVR model if needed
3. **Audio Loading**: Load audio file into processing pipeline
4. **Source Separation**: Apply AI model to separate vocal components
5. **Output Processing**: Identify and extract vocals-only audio

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
