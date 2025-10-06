# LRC Translation Module

## 🌐 Bilingual Lyrics Translation (`translate_lrc.py`)

Handles the translation of synchronized LRC lyrics to Traditional Chinese, creating bilingual LRC files that preserve timing information while providing translated content. This module uses advanced LLM prompting to maintain synchronization accuracy and ensure that translations align properly with the original timing.

## Pipeline Integration

```
Original LRC        ┌──────────────────┐    Final Bilingual
(synchronized) ───▶ │  translate_lrc   │ ───▶ Output
                   │  (this module)   │
                   └──────────────────┘
```

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

### Bilingual LRC Format

#### Format Structure
```
[mm:ss.xx]Original Japanese lyrics / Traditional Chinese translation
```

#### Example Output
```
[00:00.00]ああ 素晴らしき世界に今日も乾杯 / 啊 美好的世界今天也乾杯
[00:15.50]地球は回る 君の心に太陽が / 地球在轉動 太陽在你心中
[00:32.25]沈まないように 僕がずっと / 不讓它沉沒 我會一直
[00:45.80]君の側にいるから / 在你身邊
```

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

### Supported Languages

#### Currently Supported
- **Traditional Chinese** (primary target)
  - Full prompt template support
  - Culturally adapted translation prompts
  - Comprehensive testing and validation

#### Future Expansion Possibilities
- **Simplified Chinese**: Mainland China variant
- **English**: International accessibility
- **Korean**: K-pop and Korean music support
- **Other Languages**: Extensible architecture for additional languages

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

## Error Handling & Edge Cases

### Language Support Issues
- **Unsupported Languages**: Request for non-implemented languages
- **Missing Templates**: Prompt files not found for requested language
- **Model Limitations**: LLM doesn't support requested language pair

### Content Processing Issues
- **Malformed LRC**: Corrupted or invalid LRC file format
- **Unusual Structure**: Non-standard LRC formatting or organization
- **Length Limits**: Very long lyrics exceeding processing capacity
- **Encoding Issues**: Character encoding problems in source content

### API and Service Issues
- **Service Unavailable**: Translation API timeouts or downtime
- **Rate Limiting**: Request throttling or blocking
- **Model Errors**: Model-specific failures or limitations
- **Network Issues**: Connectivity problems affecting API calls

### Output Quality Issues
- **Timing Mismatch**: Translations don't fit within time constraints
- **Cultural Inappropriateness**: Translations not culturally suitable
- **Quality Loss**: Loss of poetic or musical qualities in translation
- **Synchronization Errors**: Timing issues in bilingual format

## Performance Considerations

### Processing Characteristics
- **API Response Time**: 15-45 seconds for translation
- **Token Usage**: Higher due to bilingual content processing
- **Memory Usage**: Moderate for text processing and formatting
- **Rate Limits**: Respects API provider limitations

### Performance Factors
- **Translation Complexity**: Complex content takes longer
- **Language Pair**: Different language pairs have different processing times
- **LLM Model Speed**: Varies by model selection and capabilities
- **Content Length**: Longer lyrics require more processing time

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

### Pipeline Integration
```python
# Used by process_lyrics.py as final processing step
from translate_lrc import main

# Add translation to Traditional Chinese
lrc_path = str(paths['lrc'])
success = main(lrc_path, str(paths['translated_lrc']), "Traditional Chinese", log_level)

if success:
    results.translation_success = True
    results.overall_success = True
    logger.info("Processing completed successfully")
else:
    results.translation_success = False
    results.error_message = "Translation failed"
    logger.error("Translation failed")
```

## API Reference

### Functions

#### `translate_lrc_content()`
Core function for translating LRC content to bilingual format.

**Parameters:**
- `client`: OpenAI-compatible client instance
- `lrc_content` (str): Complete LRC file content to translate
- `target_language` (str): Target language for translation (default: "Traditional Chinese")
- `model` (str): Model name for translation

**Returns:**
- `str`: Translated bilingual LRC content, or None if translation fails

#### `main()`
Main orchestration function for LRC translation.

**Parameters:**
- `input_path` (str): Path to input LRC file
- `output_path` (str): Path for translated output file
- `target_language` (str): Target language for translation
- `log_level` (int): Logging level for the process

**Returns:**
- `bool`: True if translation successful, False otherwise

## Output Verification

### Successful Bilingual LRC Criteria
- **Format Preservation**: Proper [mm:ss.xx] timestamp format maintained
- **Content Completeness**: Both original and translated content present
- **Translation Quality**: Natural, readable translations
- **Structure Compliance**: Proper LRC file organization
- **Length Appropriateness**: Reasonable length ratio between languages

### Quality Assessment
- **Synchronization**: Timing preserved across both languages
- **Cultural Appropriateness**: Translations suitable for target audience
- **Musical Flow**: Translations maintain musical qualities
- **Completeness**: All lyrics sections translated

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed translation analysis and API interactions
- **INFO**: Successful translations and content statistics
- **WARNING**: Quality concerns or fallback behaviors
- **ERROR**: Critical failures preventing translation

### Example Log Output
```
INFO - Translating LRC content to bilingual format...
INFO - LRC content translated successfully: 450 characters → 520 characters
WARNING - Translation to 'Simplified Chinese' not implemented, only Traditional Chinese supported
ERROR - Translation failed: API rate limit exceeded
```

## Testing & Validation

### Test Coverage
- Various LRC files and content types
- Translation quality across different musical genres
- Timing preservation verification
- Edge cases (very long/short lyrics, complex structures)
- Cultural appropriateness validation

### Validation Checklist
- [ ] Translation maintains timing synchronization
- [ ] Translated content is natural and readable
- [ ] Cultural context is appropriately handled
- [ ] LRC format compliance is maintained
- [ ] Error handling works for problematic content

## Common Pitfalls & Solutions

### Issue: "Poor translation quality"
**Symptoms:** Translations are awkward or unnatural
**Causes:**
- Poor prompt template design
- Inappropriate model selection
- Source content issues
**Solutions:**
- Review and improve prompt templates
- Consider different LLM models
- Verify source content quality

### Issue: "Translation doesn't fit timing"
**Symptoms:** Translated text is too long for time constraints
**Causes:**
- Translation expansion in target language
- Insufficient timing constraint consideration
- Prompt template not optimized for timing
**Solutions:**
- Adjust prompts for conciseness
- Consider timing constraints in prompt design
- Review translation for brevity

### Issue: "Unsupported language error"
**Symptoms:** Error when requesting non-supported languages
**Causes:**
- Language not implemented in system
- Missing prompt template for language
- Model doesn't support language pair
**Solutions:**
- Add support for requested language
- Create appropriate prompt templates
- Verify model language capabilities

### Issue: "API timeout during translation"
**Symptoms:** Translation requests time out or hang
**Causes:**
- API service overload or issues
- Very long content exceeding limits
- Network connectivity problems
**Solutions:**
- Check API service availability
- Consider content length optimization
- Verify network connectivity

## Maintenance & Development

### Language Expansion
1. **Research**: Identify target language requirements
2. **Prompt Creation**: Develop culturally appropriate prompt templates
3. **Testing**: Validate translation quality and accuracy
4. **Integration**: Add language support to module
5. **Documentation**: Update documentation with new language

### Quality Improvement
- **Regular Review**: Monitor translation quality in production
- **Prompt Optimization**: Continuously improve prompt templates
- **Model Updates**: Stay current with LLM model improvements
- **Cultural Feedback**: Incorporate user feedback for improvements

### Adding New Translation Features
1. **Feature Identification**: Determine needed translation enhancements
2. **Implementation**: Add new translation capabilities
3. **Testing**: Validate new features across content types
4. **Documentation**: Update documentation with new features

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known good LRC file
python translate_lrc.py known_good.lrc --output test_bilingual.lrc

# Enable debug logging
python translate_lrc.py input.lrc --output output.lrc --log-level DEBUG

# Check API configuration
python -c "
from utils import get_translation_config
config = get_translation_config()
print('Translation config:', config)
"
```

### Common Solutions
1. **Verify API access**: Ensure translation API is accessible and configured
2. **Check content format**: Validate input LRC file format and structure
3. **Test with simple content**: Isolate issues with content complexity
4. **Review language support**: Confirm requested language is supported

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [LRC Generation Module](generate_lrc.md) - Previous pipeline stage
- [Utils Module](utils.md) - Shared utility functions
- [Process Lyrics Module](process_lyrics.md) - Batch processing orchestrator