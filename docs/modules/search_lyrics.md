# Lyrics Search Module

## 🔍 Web Scraping Lyrics (`search_lyrics.py`)

Handles web scraping and retrieval of song lyrics from uta-net.com, Japan's largest lyrics database. This module performs intelligent searches using song titles and artist names, then extracts properly formatted lyrics with line breaks and structural information essential for LRC file generation.

## Pipeline Integration

```
Song Metadata      ┌──────────────────┐    Quality Verification
(title/artist) ───▶ │  search_lyrics   │ ───▶ (next step)
                   │  (this module)   │
                   └──────────────────┘
```

## Core Functionality

### Primary Purpose
- Search and retrieve lyrics from uta-net.com
- Implement intelligent dual-phase search strategy
- Extract properly formatted lyrics with line breaks
- Provide reference lyrics for LRC generation pipeline

### Key Features
- **Dual Search Strategy**: Title-based search with artist fallback
- **Polite Web Scraping**: Respectful scraping with rate limiting
- **Intelligent Matching**: Sophisticated song identification algorithm
- **Proper Formatting**: Preserves poetic structure and line breaks
- **Error Recovery**: Robust fallback mechanisms for failed searches

## Technical Implementation

### Dependencies
- **requests>=2.32.5**: HTTP library for web scraping
- **beautifulsoup4>=4.14.2**: HTML parsing and content extraction
- **urllib.parse**: URL encoding and manipulation
- **logging_config**: Consistent logging across pipeline

### Target Website: uta-net.com

#### Website Characteristics
- **Primary Database**: Japan's largest lyrics database
- **Content Coverage**: J-pop, anime, and traditional Japanese songs
- **HTML Structure**: Consistent layout patterns for reliable scraping
- **Size**: Comprehensive collection with millions of songs

#### Scraping Requirements
- **Respectful Rate Limiting**: 1-second delays between requests
- **Proper Headers**: Browser-like User-Agent strings
- **Error Handling**: Graceful handling of server responses
- **Structure Monitoring**: Awareness of potential layout changes

### Search Strategy Architecture

#### Phase 1: Title-Based Search
**Primary Search Method:**
- Uses song title as primary search parameter
- Searches with `Aselect=2` (title search mode)
- High precision for exact title matches
- Falls back to Phase 2 if no results found

#### Phase 2: Artist-Based Search
**Fallback Search Method:**
- Uses artist name for broader search
- Searches with `Aselect=1` (artist search mode)
- Finds other songs by same artist
- Provides alternative when title search fails

### Song Matching Algorithm

#### Matching Hierarchy
1. **Exact Match**: Both title and artist match perfectly
2. **Partial Match**: Title contains search terms
3. **Artist Match**: Same artist, different songs
4. **Fallback Selection**: First result if no clear match found

#### Selection Criteria
- **Text Content**: Link text and surrounding elements
- **Parent Elements**: Song and artist information in context
- **Pattern Recognition**: Identifies relevant song pages
- **Confidence Assessment**: Validates match quality

### Web Scraping Patterns

#### Target Elements
- **Search Endpoint**: `https://www.uta-net.com/search/`
- **Results Pattern**: Links containing `/song/` in href
- **Lyrics Container**: `div` with `id="kashi_area"`
- **Alternative Container**: `div` with class containing "kashi"

#### Content Extraction Process
1. **HTML Structure Analysis**: Identifies lyrics container elements
2. **Content Hierarchy**: Preserves line breaks and formatting
3. **Text Cleaning**: Removes HTML tags and script content
4. **Line Preservation**: Maintains poetic structure
5. **Encoding Handling**: Ensures proper UTF-8 processing

### Browser Headers Configuration

Mimics modern browser to avoid blocking:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en;q=0.9,en-US;q=0.8,de;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
```

## Code Flow & Execution

### Processing Steps
1. **Input Validation**: Validate song title and artist information
2. **Search Strategy**: Implement dual search approach (title → artist fallback)
3. **Web Request**: Send HTTP requests with proper browser headers
4. **HTML Parsing**: Use BeautifulSoup to extract relevant information
5. **Link Identification**: Find correct song page from search results
6. **Content Extraction**: Retrieve lyrics with proper formatting
7. **Text Processing**: Clean and structure lyrics content
8. **Output Formatting**: Return formatted lyrics ready for LRC generation

### Output Format Example
```
ああ 素晴らしき世界に今日も乾杯
地球は回る 君の心に太陽が
沈まないように 僕がずっと
君の側にいるから

ああ 素晴らしき世界に今日も乾杯
地球は回る 君の心に太陽が
...
```

## Error Handling & Edge Cases

### Network Issues
- **Server Unavailable**: uta-net.com timeout or downtime
- **Rate Limiting**: Anti-scraping measures or blocking
- **DNS Resolution**: Network connectivity problems
- **SSL/TLS Issues**: Certificate or security problems

### Content Issues
- **Song Not Found**: Song not in database
- **Lyrics Unavailable**: Lyrics not provided for song
- **Language Mismatch**: Content in different language
- **Premium Content**: Restricted or paywall-protected lyrics

### HTML Structure Changes
- **Layout Modifications**: Website design updates
- **Element Changes**: ID/class name modifications
- **Anti-Scraping**: Bot detection measures
- **JavaScript Content**: Dynamically rendered content

### Data Quality Issues
- **Malformed Lyrics**: Corrupted or incomplete content
- **Missing Formatting**: Lost line breaks or structure
- **Encoding Problems**: Incorrect character encoding
- **Truncated Content**: Incomplete lyrics extraction

## Performance Considerations

### Processing Characteristics
- **Request Timeout**: 10 seconds for server response
- **Page Load Time**: Variable depending on uta-net.com performance
- **Memory Usage**: Minimal for text processing
- **Network Transfer**: Small data per request

### Performance Factors
- **Success Rate**: Fast for successful searches (2-5 seconds)
- **Fallback Time**: Slower for extensive searches (10-15 seconds)
- **Website Performance**: Depends on uta-net.com response times
- **Local Processing**: Minimal computational overhead

## Usage Examples

### Standalone CLI Usage
```bash
# Search lyrics from audio file metadata
python search_lyrics.py audio.flac

# Custom output location
python search_lyrics.py audio.flac --output custom_lyrics.txt

# Debug mode for troubleshooting
python search_lyrics.py audio.flac --log-level DEBUG
```

### Programmatic Usage
```python
from search_lyrics import search_uta_net

# Basic lyrics search
lyrics = search_uta_net("Song Title", "Artist Name")

if lyrics:
    print(f"Found lyrics: {len(lyrics)} characters")
    print("First few lines:")
    print("\\n".join(lyrics.split("\\n")[:3]))
else:
    print("Lyrics not found")

# Process search results
lines = lyrics.split('\\n')
print(f"Lyrics structure: {len(lines)} lines")
```

### Pipeline Integration
```python
# Used by process_lyrics.py as fourth processing step
from search_lyrics import search_uta_net

# Search for lyrics using metadata
lyrics_content = search_uta_net(metadata['title'], metadata['artist'])

if lyrics_content:
    # Save lyrics for LRC generation
    with open(paths['lyrics_txt'], 'w', encoding='utf-8') as f:
        f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\\n")
        f.write("=" * 60 + "\\n\\n")
        f.write(lyrics_content)
        f.write(f"\\n\\nSource: uta-net.com")

    # Continue with verification
    is_match, confidence, reasoning = verify_lyrics_match(lyrics_content, transcript_content)
else:
    # Handle search failure
    logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
```

## API Reference

### Functions

#### `search_uta_net()`
Main function for searching and retrieving lyrics from uta-net.com.

**Parameters:**
- `song_title` (str): Song title to search for
- `artist_name` (str): Artist name to search for

**Returns:**
- `str`: Lyrics text if found, None otherwise

**Raises:**
- `requests.RequestException`: Network or HTTP errors
- `Exception`: General processing errors

## Output Verification

### Successful Lyrics Criteria
- **Proper Japanese Text**: Correct language and character encoding
- **Reasonable Length**: Typically 200-2000 characters for complete songs
- **Line Breaks Preserved**: Poetic structure maintained
- **Clean Content**: No HTML tags or script content
- **Appropriate Content**: Actual song lyrics, not ads or navigation

### Quality Assessment
- **Completeness**: All verses and chorus sections present
- **Accuracy**: Correct lyrics for the specified song
- **Formatting**: Proper line breaks and stanza organization
- **Encoding**: Correct UTF-8 handling of Japanese characters

## Logging & Debugging

### Log Levels
- **DEBUG**: Detailed HTTP requests and HTML parsing information
- **INFO**: Successful searches and lyrics extraction results
- **WARNING**: Fallback behaviors and minor issues
- **ERROR**: Critical failures preventing lyrics retrieval

### Example Log Output
```
INFO - Searching for: タイトル by アーティスト
INFO - Found song page: https://www.uta-net.com/song/12345/
INFO - Lyrics successfully extracted: 450 characters, 24 lines
WARNING - No results found with title search, trying artist search
ERROR - Lyrics not found on the page
```

## Testing & Validation

### Test Coverage
- Various Japanese songs and artists across genres
- Different title/artist name formats and lengths
- Search accuracy across different music categories
- Edge cases (very long/short titles, special characters)
- Fallback search mechanism validation

### Validation Checklist
- [ ] Search accuracy for known songs and artists
- [ ] Proper fallback to artist search when title fails
- [ ] Correct lyrics extraction and formatting
- [ ] Appropriate handling of special characters
- [ ] Error recovery for network and server issues

## Common Pitfalls & Solutions

### Issue: "No songs found in search results"
**Symptoms:** Search returns no results for valid songs
**Causes:**
- Incorrect song title or artist name
- Song not in uta-net.com database
- Alternative spellings or naming conventions
**Solutions:**
- Verify song title and artist accuracy
- Try alternative spellings or common variations
- Check if song exists on uta-net.com manually

### Issue: "Lyrics not found on the page"
**Symptoms:** Song page found but no lyrics extracted
**Causes:**
- Lyrics not available for this song
- Content structure different than expected
- Premium or restricted content
**Solutions:**
- Verify lyrics are available on uta-net.com
- Check for alternative lyrics sources
- Consider manual lyrics entry for rare songs

### Issue: "Connection timeout"
**Symptoms:** Requests to uta-net.com time out
**Causes:**
- Network connectivity issues
- uta-net.com server problems
- Firewall or proxy blocking requests
**Solutions:**
- Check internet connection
- Verify uta-net.com is accessible
- Try again later if server issues

### Issue: "Search request blocked"
**Symptoms:** Receiving 403 Forbidden or similar blocking responses
**Causes:**
- Anti-bot measures triggered
- Rate limiting exceeded
- Headers not mimicking real browser
**Solutions:**
- Update User-Agent headers to more recent browser
- Add longer delays between requests
- Reduce request frequency

## Maintenance & Development

### Website Monitoring
- **Layout Changes**: Monitor uta-net.com for design updates
- **Structure Changes**: Update scraping patterns as needed
- **New Features**: Adapt to new website functionality
- **Anti-Scraping**: Monitor for bot detection measures

### Search Optimization
- **Pattern Updates**: Maintain current search parameters
- **Header Updates**: Keep browser headers current
- **Rate Limiting**: Adjust delays based on server response
- **Alternative Sources**: Consider backup lyrics databases

### Adding New Sources
1. **Research**: Identify reliable alternative lyrics sources
2. **Integration**: Add new search functions following existing patterns
3. **Testing**: Validate accuracy and reliability
4. **Documentation**: Update documentation with new source information

## Troubleshooting Guide

### Quick Diagnostics
```bash
# Test with known song
python search_lyrics.py known_song.flac

# Enable debug logging
python search_lyrics.py song.flac --log-level DEBUG

# Check manual search
# Visit https://www.uta-net.com/search/ and search manually
```

### Common Solutions
1. **Verify song information**: Double-check title and artist accuracy
2. **Test search manually**: Use uta-net.com search directly
3. **Check network**: Verify internet connectivity and site availability
4. **Try variations**: Use alternative spellings or common variations

## Related Documentation

- [Main Project README](../../README.md) - Project overview and setup
- [Metadata Extraction Module](extract_metadata.md) - Previous pipeline stage
- [Lyrics Verification Module](verify_lyrics.md) - Next pipeline stage
- [Utils Module](utils.md) - Shared utility functions