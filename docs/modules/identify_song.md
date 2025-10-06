# Song Identification Module

## 🎯 ASR-Based Song Identification (`identify_song.py`)

Identifies songs from ASR (Automatic Speech Recognition) transcripts using a sophisticated combination of LLM analysis and web search. This module serves as a critical fallback mechanism when audio files lack proper metadata, enabling the pipeline to continue processing even without traditional metadata tags.

## Pipeline Integration

```
ASR Transcript    ┌──────────────────┐    Lyrics Search
(from vocals) ───▶ │  identify_song   │ ───▶ (next step)
                  │  (this module)   │
                  └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Identify songs from ASR transcript content when metadata is missing
- Use LLM analysis combined with web search for intelligent matching
- Provide fallback mechanism for pipeline continuity
- Implement retry logic with confidence-based decision making

### Key Features
- **LLM-Powered Analysis**: Advanced AI analysis of ASR transcripts
- **Web Search Integration**: SearXNG metasearch engine integration
- **Retry Mechanism**: Up to 3 attempts with feedback learning
- **Confidence Scoring**: Sophisticated confidence assessment
- **Result Caching**: JSON-based caching for performance optimization

## Technical Implementation

### Dependencies
- **pydantic_ai**: Structured LLM interactions and tool integration
- **openai**: OpenAI-compatible API client library
- **requests**: Web search API communication
- **python-dotenv**: Environment variable management
- **logging_config**: Consistent logging across pipeline

### External Service Requirements

#### SearXNG Metasearch Engine
- Must be running and accessible via `SEARXNG_URL` environment variable
- Example: `SEARXNG_URL=http://localhost:8888`
- Supports multiple search engines (Google, Bing, DuckDuckGo)
- Provides JSON API for programmatic access

#### OpenAI-Compatible API
- Requires `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`
- Supports custom endpoints for alternative providers
- Uses structured prompting for consistent results
- Configurable model selection via environment variables

### Retry Mechanism Architecture

Implements sophisticated retry system with progressive enhancement:

**Attempt 1**: Standard identification using ASR transcript
- Direct LLM analysis of transcript content
- Web search integration for context
- High confidence threshold (> 0.7)
- Immediate success path for clear matches

**Attempt 2**: Enhanced search with refined queries
- LLM generates optimized search queries
- Expanded search parameters and context
- Medium confidence threshold (> 0.5)
- Learning from previous attempt results

**Attempt 3**: Final attempt with maximum flexibility
- Broadest search parameters and context
- Lowest confidence threshold (> 0.3)
- Maximum effort for difficult cases
- Graceful failure if no acceptable match found

### Confidence Thresholds

| Threshold Level | Score Range | Behavior |
|----------------|-------------|----------|
| **High Confidence** | > 0.7 | Immediate acceptance, no retries needed |
| **Medium Confidence** | 0.5-0.7 | Acceptance after retry attempts |
| **Low Confidence** | 0.3-0.5 | Final attempt only, flagged for review |
| **Rejection** | ≤ 0.3 | Insufficient confidence, stop processing |

### Search Strategy

1. **Primary Search**: Direct ASR transcript content analysis
2. **Query Enhancement**: LLM generates optimized search queries
3. **Result Processing**: Extracts relevant information from search results
4. **Pattern Matching**: Identifies song titles, artists, and languages
5. **Confidence Assessment**: Multi-factor scoring algorithm

### Caching System

**Cache File Format:**
```json
{
  "song_title": "Song Title",
  "artist_name": "Artist Name",
  "confidence_score": 0.85,
  "search_queries_used": ["query1", "query2"],
  "reasoning": "LLM explanation of identification",
  "attempt_number": 1,
  "total_attempts": 3
}
```

**Cache Benefits:**
- Eliminates redundant API calls for known songs
- Enables skip functionality in batch processing
- Preserves successful identifications across sessions
- Supports debugging and result analysis

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Verify transcript content and configuration
2. **LLM Configuration**: Set up OpenAI-compatible API client
3. **Prompt Engineering**: Load structured prompt template
4. **Web Search Integration**: Query SearXNG metasearch engine
5. **LLM Analysis**: Process search results with AI
6. **Confidence Scoring**: Validate against thresholds
7. **Retry Logic**: Implement up to 3 attempts with feedback
8. **Result Caching**: Save successful identifications

### Output Format
Returns tuple with song information:
```python
(song_title: str, artist_name: str, native_language: str)
# or None if identification fails after all retry attempts
```

## Error Handling & Edge Cases

### Network Issues
- **SearXNG server unavailable**: Timeout and connection errors
- **API rate limiting**: Temporary failures and throttling
- **Network connectivity**: DNS resolution and connectivity problems

### Content Issues
- **Empty transcripts**: Invalid or missing ASR content
- **Non-musical content**: Spoken word or non-song material
- **Multiple languages**: Mixed language content in single transcript
- **Poor audio quality**: ASR transcription errors affecting identification

### API Issues
- **Invalid credentials**: API key or endpoint configuration errors
- **Model unavailability**: Model-specific errors or downtime
- **Token limits**: Long transcripts exceeding processing limits
- **Malformed responses**: Unexpected API response formats

### Configuration Issues
- **Missing environment variables**: Required configuration not set
- **Invalid SearXNG URL**: Malformed or unreachable search endpoint
- **Unsupported models**: Incompatible model specifications

## Performance Considerations

### Optimization Features
- **Retry delays**: Prevents overwhelming external services
- **Result caching**: Minimizes redundant operations
- **Search result limits**: Top 10 results for efficiency
- **Transcript truncation**: Manages token usage for long content
- **Connection pooling**: Efficient HTTP request management

### Performance Characteristics
- **Response Time**: 10-30 seconds per identification attempt
- **Network Usage**: Moderate (web search + API calls)
- **Memory Usage**: Minimal for text processing
- **Scalability**: Efficient for batch processing with caching

## Usage Examples

### Standalone CLI Usage
```bash
# Identify song from transcript text
python identify_song.py --transcript "ASR transcript content here"

# Identify from transcript file
python identify_song.py --file transcript.txt

# With custom result caching
python identify_song.py --file transcript.txt --result-file cache.json
```

### Programmatic Usage
```python
from identify_song import identify_song_from_asr_with_retry

# Basic identification
result = identify_song_from_asr_with_retry(transcript_text, max_retries=3)

if result:
    song_title, artist_name, language = result
    print(f"Identified: {song_title} by {artist_name} ({language})")
else:
    print("Could not identify song from transcript")

# With caching for performance
result = identify_song_from_asr_with_retry(
    transcript_text,
    result_file_path="cache/song_id.json",
    force_recompute=False
)
```

### Pipeline Integration
```python
# Used by process_lyrics.py when metadata is missing
from identify_song import identify_song_from_asr_with_retry

# Attempt song identification from ASR transcript
identified_song = identify_song_from_asr_with_retry(
    transcript_content,
    result_file_path=song_id_cache_path,
    force_recompute=not resume_mode,
    max_retries=3
)

if identified_song:
    song_title, artist_name, native_language = identified_song
    # Update metadata and continue with lyrics search
    metadata['title'] = song_title
    metadata['artist'] = artist_name
```

## API Reference

### Core Classes

#### `SongIdentification(BaseModel)`
Structured output model for identification results.

**Fields:**
- `song_title` (str): Identified song title in native language
- `artist_name` (str): Identified artist name in native language
- `confidence_score` (float): Confidence score 0.0-1.0
- `native_language` (str): Native language of song (e.g., 'Japanese')
- `search_queries_used` (List[str]): Search queries that were used
- `reasoning` (str): Explanation of identification decision

#### `SongIdentifier`
Main class for song identification operations.

**Methods:**
- `__init__()`: Initialize with LLM and search tools
- `identify_song(transcript: str)`: Perform single identification attempt

### Functions

#### `identify_song_from_asr_with_retry()`
Main identification function with retry mechanism.

**Parameters:**
- `transcript` (str): ASR transcript content
- `result_file_path` (Optional[str]): Cache file path
- `force_recompute` (bool): Skip cache if True
- `max_retries` (int): Maximum retry attempts (default: 3)

**Returns:**
- `Optional[Tuple[str, str, str]]`: (title, artist, language) or None

#### `searxng_search()`
Web search utility function using SearXNG.

**Parameters:**
- `query` (str): Search query string

**Returns:**
- `str`: Formatted search results for LLM processing

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed API interactions and prompt engineering
- **INFO**: Successful identifications and confidence scores
- **WARNING**: Low confidence results and retry attempts
- **ERROR**: Critical failures and configuration issues

### Example Log Output
```
INFO - Song identification attempt 1/3
INFO - Successfully identified song: 'Song Title' by 'Artist Name' (Japanese) - confidence: 0.85
WARNING - Low confidence identification: 0.35 for 'Maybe Title' by 'Maybe Artist'
ERROR - SearXNG search failed: Connection timeout
DEBUG - Running song identification with Pydantic AI agent
```

## Testing & Validation

### Test Coverage
- Various transcript qualities and lengths
- Different music genres and languages
- Retry mechanism functionality
- Caching behavior and persistence
- Error conditions and edge cases

### Validation Checklist
- [ ] Proper identification of clear, high-quality transcripts
- [ ] Appropriate fallback behavior for poor quality transcripts
- [ ] Correct retry logic with progressive enhancement
- [ ] Cache functionality works correctly
- [ ] Error handling for external service failures

## Common Pitfalls & Solutions

### Issue: "SearXNG search timed out"
**Symptoms:** Search requests fail with timeout errors
**Causes:**
- SearXNG server unavailable or overloaded
- Network connectivity issues
- Incorrect SEARXNG_URL configuration
**Solutions:**
- Verify SearXNG server status and URL
- Check network connectivity
- Review server logs for issues

### Issue: "Low confidence identifications"
**Symptoms:** Valid songs identified with low confidence scores
**Causes:**
- Poor quality ASR transcripts
- Uncommon or obscure songs
- Language or cultural barriers
**Solutions:**
- Review ASR transcript quality
- Consider adjusting confidence thresholds
- Verify song exists in searchable databases

### Issue: "No search results found"
**Symptoms:** Search queries return no results
**Causes:**
- SearXNG configuration issues
- Network connectivity problems
- Song not available in search engines
**Solutions:**
- Verify SearXNG configuration
- Check network connectivity
- Try alternative search terms or spellings

### Issue: "API key not found"
**Symptoms:** Authentication errors with LLM API
**Causes:**
- Missing or invalid API configuration
- Incorrect environment variable setup
- API service issues
**Solutions:**
- Verify .env file configuration
- Check API key validity
- Confirm API service availability

## Maintenance & Development

### Environment Configuration
```bash
# Required environment variables
OPENAI_BASE_URL=https://your-api-endpoint.com
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=your-preferred-model

# Optional SearXNG configuration
SEARXNG_URL=http://localhost:8888
```

### Adding New Search Engines
1. Update SearXNG engine configuration in search parameters
2. Test search quality and relevance
3. Update documentation with new engine information
4. Consider rate limiting implications

### Updating Confidence Thresholds
1. Analyze identification accuracy across test cases
2. Adjust thresholds based on real-world performance
3. Update documentation with new threshold values
4. Consider different thresholds for different use cases

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with sample transcript
python identify_song.py --transcript "sample transcript text"

# Enable debug logging
python identify_song.py --transcript "text" --log-level DEBUG

# Test with file input
python identify_song.py --file transcript.txt
```

### Common Solutions
1. **Verify external services**: Check SearXNG and API availability
2. **Review transcript quality**: Poor ASR affects identification accuracy
3. **Check configuration**: Verify environment variables and settings
4. **Test with known content**: Use transcripts from known songs for validation

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Search Lyrics Module](search_lyrics.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions
- [Process Lyrics Module](process_lyrics.md) - Batch processing orchestrator