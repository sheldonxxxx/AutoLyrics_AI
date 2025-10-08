# Song Identification Module

## 🎯 ASR-Based Song Identification (`identify_song.py`)

Identifies songs from ASR (Automatic Speech Recognition) transcripts using a sophisticated combination of LLM analysis and web search. This module serves as a critical fallback mechanism when audio files lack proper metadata, enabling the pipeline to continue processing even without traditional metadata tags.

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

### Environment Configuration
```bash
# Required environment variables
OPENAI_BASE_URL=https://your-api-endpoint.com
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=your-preferred-model

# Optional SearXNG configuration
SEARXNG_URL=http://localhost:8888
```
