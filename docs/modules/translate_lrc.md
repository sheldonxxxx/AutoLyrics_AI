# LRC Translation Module

## 🌐 Bilingual Lyrics Translation (`translate_lrc.py`)

Handles the translation of synchronized LRC lyrics to Traditional Chinese, creating bilingual LRC files that preserve timing information while providing translated content. This module uses advanced LLM prompting to maintain synchronization accuracy and ensure that translations align properly with the original timing.

## Core Functionality

### Primary Purpose
- Translate synchronized LRC files to Traditional Chinese
- Create bilingual LRC files with preserved timing
- Maintain synchronization accuracy across languages
- Provide international accessibility for lyrics content

### Key Features
- **Bilingual LRC Format**: Synchronized original and translated lyrics
- **Timing Preservation**: Maintains precise [mm:ss.xx] timestamps
- **Cultural Adaptation**: Contextually appropriate translations
- **Flexible API Support**: OpenAI-compatible translation services
- **Quality Validation**: LRC format compliance checking

## Technical Implementation

### Dependencies
- **openai**: OpenAI-compatible API client library
- **python-dotenv**: Environment variable management
- **logging_config**: Consistent logging across pipeline
- **utils**: Shared utility functions for file I/O and validation

### Translation Strategy

#### 1. Context Preservation
- **Poetic Maintenance**: Preserves musical and poetic context
- **Rhyme Consideration**: Maintains rhyme and rhythm where possible
- **Cultural Appropriateness**: Considers cultural context and sensitivity

#### 2. Timing Synchronization
- **Time Constraints**: Ensures translations fit within timing windows
- **Readability Maintenance**: Maintains readability at song tempo
- **Length Management**: Handles varying line lengths appropriately

#### 3. Cultural Adaptation
- **Reference Adaptation**: Appropriately adapts cultural references
- **Emotional Preservation**: Maintains emotional impact of original
- **Audience Consideration**: Considers target audience expectations

### Prompt Engineering

#### Template Location
- **Primary Template**: `prompt/lrc_traditional_chinese_prompt.txt`
- **Language Mapping**: `utils.get_prompt_file_for_language()`

#### Key Prompt Components
- **Translation Instructions**: Clear bilingual requirements
- **Cultural Context**: Japanese music and lyrics background
- **Timing Constraints**: Synchronization preservation requirements
- **Output Format**: Proper bilingual LRC structure
- **Quality Standards**: Accuracy and naturalness requirements

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Validate LRC file exists and is readable
2. **Content Parsing**: Read and analyze LRC file structure
3. **Translation Configuration**: Set up translation-specific API client
4. **Language Support**: Validate target language compatibility
5. **Prompt Engineering**: Load appropriate translation prompt template
6. **Bilingual Generation**: Create synchronized bilingual LRC content
7. **Format Preservation**: Maintain LRC timing and structure
8. **Output Validation**: Ensure translated LRC meets format requirements

### API Configuration Flexibility

#### Translation-Specific Settings
```bash
# Dedicated translation service
TRANSLATION_BASE_URL=https://translation-api.example.com
TRANSLATION_API_KEY=your-translation-api-key
TRANSLATION_MODEL=specialized-translation-model
```

#### Fallback to General Settings
```bash
# Falls back to general OpenAI settings if translation-specific not available
OPENAI_BASE_URL=https://api.example.com
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=general-purpose-model
```

## Usage Examples

### Standalone CLI Usage
```bash
# Basic translation to Traditional Chinese
python translate_lrc.py input.lrc --output bilingual.lrc --language "Traditional Chinese"

# Custom output filename
python translate_lrc.py song.lrc -o song_traditional_chinese.lrc

# Debug mode for troubleshooting
python translate_lrc.py input.lrc --log-level DEBUG
```

### Programmatic Usage
```python
from translate_lrc import main

# Basic translation
success = main("input.lrc", "output.lrc", "Traditional Chinese")

if success:
    print("Translation completed successfully")
else:
    print("Translation failed")

# With custom logging level
import logging
success = main(
    "input.lrc",
    "output.lrc",
    "Traditional Chinese",
    log_level=logging.DEBUG
)
```
