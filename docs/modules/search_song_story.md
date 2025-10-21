# Search Song Story

## Overview

The Search Song Story module provides functionality to search for background stories about songs, including:
- Anime/TV show theme song context
- Story behind the song creation
- Cultural or historical significance
- Artist background related to the song
- Any other relevant contextual information

The module uses LLM-powered analysis combined with web search tools to find detailed background information about identified songs, with special focus on identifying if the song is a theme for anime, TV shows, or other media.

## Pipeline Integration

The Search Song Story module integrates into the Music Lyrics Processing Pipeline as stage 2.5/6 (after song identification but before LRC generation). It works in conjunction with the identify_song module to provide additional context about identified songs.

```
[Input FLAC Files] → [extract_metadata.py] → [identify_song.py] → [search_song_story.py] → [search_lyrics.py] → [generate_lrc.py] → [translate_lrc.py] → [Output LRC Files]
```

## Technical Implementation

### Dependencies
- `pydantic_ai` (structured LLM interactions)
- `openai` (API client library)
- `dotenv` (environment variable management)
- `logging_config` (pipeline logging)
- `utils` (file operations and validation)

### External Services
- Remote MCP SearXNG server for web search
- OpenAI-compatible API (requires OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL)

### Core Classes

#### SongStory
Structured output model for song background story results with fields:
- `song_title`: The song title in its native language
- `artist_name`: The artist name in its native language
- `native_language`: The native language of the song
- `story_type`: Type of story found (e.g., 'anime_theme', 'tv_show_theme', 'creation_story', 'cultural_significance', 'artist_background')
- `story_summary`: Detailed summary of the song's background story
- `story_details`: Complete detailed story information
- `confidence_score`: Confidence score between 0.0 and 1.0
- `search_queries_used`: List of search queries that were used
- `sources_used`: List of sources/URLs used for the story
- `reasoning`: Explanation of how the story was identified and verified

#### SongStorySearcher
Main class that orchestrates the story search process:
- Initializes LLM and MCP search tools
- Performs story search using title, artist, and language information
- Handles caching and result validation
- Returns structured story information

### Key Functions

#### search_song_story_from_identification()
Main entry point for searching song stories with caching support:
- Takes song title, artist name, native language, and output paths
- Supports resume functionality through caching
- Returns detailed story information if found

## Usage Examples

### Command Line Interface
```bash
python search_song_story.py --title "Gurenge" --artist "LiSA" --language "Japanese"
```

### Programmatic Usage
```python
from search_song_story import search_song_story_from_identification

paths = {
    'song_story': 'path/to/story_result.json'
}

result = search_song_story_from_identification(
    song_title="Gurenge", 
    artist_name="LiSA", 
    native_language="Japanese",
    paths=paths
)

if result:
    story_type, story_summary, story_details, sources_used, reasoning, confidence_score = result
    print(f"Story Type: {story_type}")
    print(f"Summary: {story_summary}")
    print(f"Details: {story_details}")
```

### Pipeline Integration
The module is automatically called from identify_song.py after successful song identification:
```python
# In identify_song.py
story_result = search_song_story_from_identification(
    result.song_title, 
    result.artist_name, 
    result.native_language, 
    paths, 
    force_recompute=not force_recompute,
    max_search_results=max_search_results
)
```

## API Reference

### Command Line Arguments
- `--title, -t`: Song title (required)
- `--artist, -a`: Artist name (required)
- `--language, -l`: Native language of the song (required)
- `--result-file, -r`: File to save/load song story results
- `--max-search-results`: Maximum number of search results to return (default: 5)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--logfire`: Enable Logfire integration

### Environment Variables
- `OPENAI_BASE_URL`: Base URL for OpenAI-compatible API
- `OPENAI_API_KEY`: API key for OpenAI-compatible service
- `OPENAI_MODEL`: Model name for LLM interactions
- `MCP_SEARXNG_SERVER_URL`: URL for MCP SearXNG server (optional)
- `SEARXNG_URL`: URL for SearXNG instance (used if MCP_SEARXNG_SERVER_URL not set)

## Troubleshooting

### Common Issues

#### Missing Environment Variables
Ensure all required environment variables are set:
```bash
export OPENAI_BASE_URL="your_api_url"
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="your_model_name"
```

#### Low Confidence Results
If story search returns low confidence results, try:
- Ensuring the song title and artist name are correctly identified
- Verifying the native language is accurate
- Checking that the MCP SearXNG server is accessible

#### Search Limitations
- The module relies on web search results, so obscure or very new songs may not have background stories available
- Results may vary based on the quality of the search queries generated by the LLM
- Some stories may be in the native language of the song, requiring translation

### Error Messages
- "Missing required parameters": Ensure song_title, artist_name, and native_language are provided
- "Failed to load song story search prompt template": Check that prompt/song_story_search_prompt.txt exists
- "Invalid confidence score": The LLM returned an invalid confidence score