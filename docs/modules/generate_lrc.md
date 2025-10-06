# LRC Generation Module

## 📝 Synchronized Lyrics Generation (`generate_lrc.py`)

This module is the core of the Music Lyrics Processing Pipeline, responsible for generating synchronized LRC (Lyrics) files by intelligently combining reference lyrics with ASR transcript timestamps. It uses advanced LLM prompting to align lyrics with precise timing information, creating professional-quality synchronized lyrics for music playback applications.

## Pipeline Integration

```
Lyrics +           ┌──────────────────┐    Translation
ASR Timestamps ───▶ │  generate_lrc    │ ───▶ (next step)
                   │  (this module)   │
                   └──────────────────┘
```

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

## Error Handling & Edge Cases

### Content Quality Issues
- **Missing Content**: Incomplete lyrics or transcript data
- **Poor ASR Quality**: Low-quality speech recognition results
- **Language Mismatch**: Lyrics in different language than expected
- **Corrupted Data**: Malformed or unreadable input files

### API Processing Issues
- **Timeout Errors**: API request timeouts or delays
- **Rate Limiting**: API service throttling or blocking
- **Model Errors**: Model unavailability or processing failures
- **Token Limits**: Content too long for API processing

### Alignment Challenges
- **Structure Mismatch**: Different structure between lyrics and transcript
- **Timing Discrepancies**: Inconsistent timing between sources
- **Cultural Variations**: Linguistic or cultural differences
- **Artistic Content**: Creative vs. literal interpretations

### Output Validation Issues
- **Format Errors**: Generated LRC doesn't meet format requirements
- **Timing Issues**: Inconsistencies in timestamp progression
- **Encoding Problems**: Character encoding issues in output
- **File I/O Errors**: Problems saving generated content

## Performance Considerations

### Processing Characteristics
- **API Response Time**: 10-30 seconds for LRC generation
- **Token Usage**: Moderate to high for complex songs
- **Memory Usage**: Minimal for text processing operations
- **Rate Limits**: Respects API provider limitations

### Performance Factors
- **Simple Songs**: Fast processing for clear, structured content
- **Complex Songs**: Slower processing for detailed alignment needs
- **LLM Model Speed**: Depends on model selection and complexity
- **Content Length**: Longer songs require more processing time

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

### Pipeline Integration
```python
# Used by process_lyrics.py as fifth processing step
from generate_lrc import generate_lrc_lyrics, correct_grammar_in_transcript

# Generate LRC with reference lyrics (preferred)
if lyrics_content:
    lrc_lyrics = generate_lrc_lyrics(client, lyrics_content, asr_transcript, model)
elif corrected_transcript_content:
    # Fallback to corrected transcript
    lrc_lyrics = generate_lrc_lyrics(client, corrected_transcript_content, asr_transcript, model)
else:
    # Final fallback to raw transcript
    lrc_lyrics = convert_transcript_to_lrc(asr_transcript)

if lrc_lyrics:
    # Save LRC file
    with open(paths['lrc'], 'w', encoding='utf-8') as f:
        f.write(lrc_lyrics)
    results.lrc_generation_success = True
else:
    # Handle generation failure
    results.lrc_generation_success = False
    results.error_message = "LRC generation returned no content"
```

## API Reference

### Functions

#### `generate_lrc_lyrics()`
Main function for generating LRC content from lyrics and transcript.

**Parameters:**
- `client`: OpenAI client instance
- `lyrics_text` (str): Downloaded lyrics text
- `asr_transcript` (str): ASR transcript with timestamps
- `model` (str): Model name for generation

**Returns:**
- `str`: LRC formatted lyrics content

#### `correct_grammar_in_transcript()`
Correct grammatical errors in ASR transcripts.

**Parameters:**
- `client`: OpenAI client instance
- `asr_transcript` (str): Raw ASR transcript with potential errors
- `filename` (str, optional): Original audio filename for context
- `model` (str): Model name for correction

**Returns:**
- `str`: Grammatically corrected transcript

## Output Verification

### Successful LRC Criteria
- **Proper Format**: Valid [mm:ss.xx] timestamp format
- **Timing Progression**: Chronological order, proper sequencing
- **Content Quality**: Meaningful lyrics synchronized with timing
- **Structure Compliance**: Proper LRC file organization
- **Length Appropriateness**: Matches source material length

### Quality Assessment
- **Synchronization**: Lyrics timing matches audio content
- **Readability**: Text is clear and properly formatted
- **Completeness**: All major lyrics sections included
- **Accuracy**: Content matches source material

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed alignment analysis and LLM interactions
- **INFO**: Successful generation and timing information
- **WARNING**: Quality issues or fallback usage
- **ERROR**: Critical failures preventing LRC generation

### Example Log Output
```
INFO - Generating LRC formatted lyrics...
INFO - LRC lyrics generated successfully: 45 lines, timestamps preserved
WARNING - Using transcript-only alignment (no reference lyrics available)
ERROR - LRC generation failed: API timeout
```

## Testing & Validation

### Test Coverage
- Various lyrics and transcript combinations
- Different music genres and complexity levels
- Edge cases (very long/short content, poor quality inputs)
- Grammar correction effectiveness
- LRC format compliance across scenarios

### Validation Checklist
- [ ] Proper timestamp format in generated LRC
- [ ] Meaningful lyrics synchronization
- [ ] Grammar correction improves readability
- [ ] Fallback methods work when primary fails
- [ ] Output meets LRC format specifications

## Common Pitfalls & Solutions

### Issue: "Poor timing alignment in output"
**Symptoms:** Generated LRC has incorrect or inconsistent timing
**Causes:**
- Poor quality ASR transcript
- Inaccurate reference lyrics
- Complex song structure
**Solutions:**
- Review ASR transcript quality first
- Verify reference lyrics accuracy
- Consider manual timing adjustment for complex cases

### Issue: "LRC format errors in output"
**Symptoms:** Generated content doesn't follow LRC format
**Causes:**
- Input data format issues
- Prompt template problems
- API response formatting errors
**Solutions:**
- Validate input data format
- Check prompt template integrity
- Review API response parsing

### Issue: "Generation timeout"
**Symptoms:** LRC generation takes extremely long or hangs
**Causes:**
- API service issues or overload
- Very long content exceeding limits
- Network connectivity problems
**Solutions:**
- Check API service availability
- Consider content length optimization
- Verify network connectivity

### Issue: "Inconsistent results"
**Symptoms:** Same inputs produce different LRC outputs
**Causes:**
- Non-deterministic LLM responses
- API service instability
- Temperature settings too high
**Solutions:**
- Review LLM model selection
- Lower temperature settings for consistency
- Check for API service issues

## Maintenance & Development

### Prompt Template Management
- **Regular Updates**: Maintain current prompt templates
- **Performance Monitoring**: Track template effectiveness
- **A/B Testing**: Consider prompt variations for optimization
- **Model Compatibility**: Ensure compatibility with LLM updates

### API Configuration
- **Flexible Setup**: Support multiple API providers
- **Configuration Management**: Environment-based configuration
- **Fallback Support**: Graceful degradation for API issues
- **Performance Optimization**: API usage optimization

### Adding New Output Formats
1. **Research**: Identify additional lyrics format requirements
2. **Implementation**: Add format conversion functions
3. **Testing**: Validate format compliance and accuracy
4. **Documentation**: Update documentation with new format support

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known good inputs
python generate_lrc.py --lyrics-file good_lyrics.txt --transcript-file good_transcript.txt --output test.lrc

# Enable debug logging
python generate_lrc.py --lyrics-file lyrics.txt --transcript-file transcript.txt --output output.lrc --log-level DEBUG

# Test grammar correction separately
python -c "
from generate_lrc import correct_grammar_in_transcript
from openai import OpenAI
client = OpenAI(base_url='your-url', api_key='your-key')
result = correct_grammar_in_transcript(client, 'test transcript', model='your-model')
print('Correction result:', result)
"
```

### Common Solutions
1. **Verify input quality**: Check both lyrics and transcript for readability
2. **Test API connectivity**: Ensure API service is accessible
3. **Review content length**: Very long content may cause issues
4. **Check model selection**: Different models may perform differently

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Lyrics Verification Module](verify_lyrics.md) - Previous pipeline stage
- [Translation Module](translate_lrc.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions