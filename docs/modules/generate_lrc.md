# LRC Generation Module

## 📝 Synchronized Lyrics Generation (`generate_lrc.py`)

This module is the core of the Music Lyrics Processing Pipeline, responsible for generating synchronized LRC (Lyrics) files by intelligently combining reference lyrics with ASR transcript timestamps. It uses advanced LLM prompting to align lyrics with precise timing information, creating professional-quality synchronized lyrics for music playback applications.

## Core Functionality

### Primary Purpose
- Generate synchronized LRC files from lyrics and ASR timestamps
- Use AI for intelligent timing alignment and lyrics synchronization
- Provide core functionality for creating karaoke-ready lyrics
- Support both reference lyrics and transcript-only generation

### Key Features
- **Intelligent Alignment**: AI-powered lyrics-to-timing synchronization
- **Dual Input Support**: Works with or without reference lyrics
- **Grammar Correction**: Built-in ASR transcript correction
- **LRC Format Compliance**: Proper [mm:ss.xx] timestamp formatting
- **Flexible API Support**: OpenAI-compatible API integration

## Technical Implementation

### Dependencies
- **openai**: OpenAI-compatible API client library
- **python-dotenv**: Environment variable management
- **logging_config**: Consistent logging across pipeline
- **utils**: Shared utility functions for file I/O and validation

### LRC Format Specification

#### Standard LRC Format
```
[mm:ss.xx]Line 1 lyrics
[mm:ss.xx]Line 2 lyrics
[mm:ss.xx]Line 3 lyrics
```

#### Format Components
- **mm**: Minutes (00-99)
- **ss**: Seconds (00-59)
- **xx**: Hundredths of seconds (00-99)
- **Lyrics**: Text content following timestamp

#### Example Output
```
[00:00.00]ああ 素晴らしき世界に今日も乾杯
[00:15.50]地球は回る 君の心に太陽が
[00:32.25]沈まないように 僕がずっと
[00:45.80]君の側にいるから
```

### Alignment Strategy

#### 1. Reference-Based Alignment
- **Primary Method**: Uses downloaded lyrics as structural reference
- **Timing Mapping**: Maps ASR transcript timing to reference lyrics
- **Structure Preservation**: Maintains poetic structure and line breaks
- **Quality Focus**: Produces highest quality synchronized output

#### 2. Timestamp Preservation
- **ASR Accuracy**: Maintains precise timing from speech recognition
- **Singing Adjustment**: Accounts for singing vs. speaking differences
- **Tempo Handling**: Manages varying tempo and rhythm patterns

#### 3. Content Reconciliation
- **Phrase Matching**: Identifies similar phrases between sources
- **Pronunciation Handling**: Manages pronunciation variations
- **Meaning Preservation**: Maintains meaning while optimizing timing

### Grammar Correction Capability

#### Purpose
- Correct recognition errors in ASR transcripts
- Improve readability and accuracy of generated content
- Provide fallback when reference lyrics are unavailable

#### Process
1. **Error Detection**: Identify grammatical issues in transcripts
2. **Contextual Correction**: Use LLM for intelligent error correction
3. **Meaning Preservation**: Maintain original intent and content
4. **Japanese Optimization**: Specialized prompts for Japanese text

### Prompt Engineering

#### Template Location
- **Primary Template**: `prompt/lrc_generation_prompt.txt`
- **Grammar Template**: `prompt/grammatical_correction_prompt.txt`

#### Key Prompt Components
- **Task Definition**: Clear LRC generation instructions
- **Input Format**: Structured lyrics + transcript format
- **Alignment Guidelines**: Systematic timing alignment approach
- **Output Format**: Proper LRC syntax requirements
- **Quality Standards**: Accuracy and formatting requirements

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Validate lyrics and transcript data availability
2. **Data Preparation**: Convert ASR transcript to LRC-compatible format
3. **LLM Configuration**: Set up OpenAI-compatible API client
4. **Prompt Engineering**: Load specialized LRC generation prompt template
5. **Content Alignment**: Use LLM to intelligently align lyrics with timestamps
6. **LRC Formatting**: Ensure proper LRC syntax and structure
7. **Grammar Correction**: Provide fallback correction for ASR transcripts
8. **Output Generation**: Produce properly formatted LRC file content

### Dual Input Processing

#### Scenario 1: With Reference Lyrics
- **Primary Method**: Uses downloaded lyrics as reference
- **Alignment Process**: Maps transcript timing to reference structure
- **Quality Output**: Highest quality synchronized lyrics
- **Structure Preservation**: Maintains original poetic structure

#### Scenario 2: Without Reference Lyrics
- **Fallback Method**: Uses corrected transcript only
- **Direct Conversion**: Converts transcript directly to LRC format
- **Timing Focus**: Preserves ASR timing information
- **Value Addition**: Still provides synchronized timing data

## Usage Examples

### Standalone CLI Usage
```bash
# Generate LRC from lyrics and transcript files
python generate_lrc.py --lyrics-file lyrics.txt --transcript-file transcript.txt --output song.lrc

# With custom logging
python generate_lrc.py --lyrics-file lyrics.txt --transcript-file transcript.txt --output song.lrc --log-level DEBUG
```

### Programmatic Usage
```python
from generate_lrc import generate_lrc_lyrics
from openai import OpenAI

# Initialize API client
client = OpenAI(base_url="your-api-url", api_key="your-key")

# Generate LRC content
lrc_content = generate_lrc_lyrics(
    client=client,
    lyrics_text=lyrics,
    asr_transcript=transcript,
    model="your-model"
)

if lrc_content:
    # Save to file
    with open("output.lrc", 'w', encoding='utf-8') as f:
        f.write(lrc_content)
    print("LRC file generated successfully")
else:
    print("LRC generation failed")

# Grammar correction example
from generate_lrc import correct_grammar_in_transcript

corrected = correct_grammar_in_transcript(
    client=client,
    asr_transcript=raw_transcript,
    filename="song.flac",
    model="your-model"
)
```

