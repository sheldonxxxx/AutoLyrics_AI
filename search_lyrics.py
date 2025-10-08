#!/usr/bin/env python3
"""
Search for lyrics on uta-net.com using song title and artist name.

This module handles web scraping for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/search_lyrics.md

Key Features:
- Dual search strategy (title → artist fallback)
- Polite web scraping with rate limiting
- Intelligent song matching algorithm
- Proper Japanese text formatting and encoding

Dependencies:
- requests>=2.32.5 (HTTP web scraping)
- beautifulsoup4>=4.14.2 (HTML parsing)
- logging_config (pipeline logging)

Target Site: uta-net.com (Japan's largest lyrics database)

Pipeline Stage: 4/6 (Lyrics Search)
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import os
import logging
from logging_config import setup_logging, get_logger
from extract_metadata import extract_metadata

logger = get_logger(__name__)

def search_uta_net(song_title, artist_name):
    """
    Search for lyrics on uta-net.com using song title and artist name.
    
    Args:
        song_title (str): Song title to search for
        artist_name (str): Artist name to search for
        
    Returns:
        str: Lyrics if found, None otherwise
    """
    # Format the search URL based on our Puppeteer exploration
    search_url = "https://www.uta-net.com/search/"
    
    # Prepare search parameters based on what we found
    # Aselect=2 is for title search, and we can add artist as well
    search_params = {
        'Aselect': 2,  # Search for title
        'Keyword': song_title,
    }
    
    # Encode the parameters
    encoded_params = urllib.parse.urlencode(search_params)
    full_search_url = f"{search_url}?{encoded_params}"
    
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en;q=0.9,en-US;q=0.8,de;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make the search request
        logger.info(f"Searching for: {song_title} by {artist_name}")
        logger.info(f"URL: {full_search_url}")
        
        response = requests.get(full_search_url, headers=headers)
        response.raise_for_status()
        
        # Parse the search results page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for song links in the search results
        # Uta-net search results typically have links to song pages
        song_links = soup.find_all('a', href=lambda x: x and '/song/' in x)
        
        # If we don't find results with title search, try artist search
        if not song_links:
            logger.info("No results found with title search, trying artist search...")
            search_params = {
                'Aselect': 1,  # Search for artist
                'Keyword': artist_name,
            }
            encoded_params = urllib.parse.urlencode(search_params)
            full_search_url = f"{search_url}?{encoded_params}"
            
            logger.info(f"Searching for artist: {artist_name}")
            logger.info(f"URL: {full_search_url}")
            
            response = requests.get(full_search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            song_links = soup.find_all('a', href=lambda x: x and '/song/' in x)
        
        if not song_links:
            logger.warning("No songs found in search results.")
            return None
        
        # Look for the specific song in the results
        target_song_url = None
        for link in song_links:
            # Get the text content of the link or surrounding elements to match the song title
            link_text = link.get_text().strip()
            
            # Also check parent elements for song/artist info
            parent = link.parent
            if parent:
                parent_text = parent.get_text().strip()
                
                # Check if this link corresponds to our target song
                if song_title in parent_text and artist_name in parent_text:
                    target_song_url = urllib.parse.urljoin('https://www.uta-net.com/', link['href'])
                    break
        
        # If we couldn't find the specific song, just take the first one
        if not target_song_url:
            logger.info(f"Could not find specific song '{song_title}', taking first result...")
            relative_song_url = song_links[0]['href']
            target_song_url = urllib.parse.urljoin('https://www.uta-net.com/', relative_song_url)
        
        logger.info(f"Found song page: {target_song_url}")
        
        # Fetch the song page
        time.sleep(1)  # Be respectful to the server
        song_response = requests.get(target_song_url, headers=headers)
        song_response.raise_for_status()
        
        # Parse the song page to extract lyrics
        song_soup = BeautifulSoup(song_response.text, 'html.parser')
        
        # Look for the lyrics container
        # On uta-net.com, lyrics are typically in a div with id "kashi_area"
        lyrics_div = song_soup.find('div', id='kashi_area')
        
        if not lyrics_div:
            logger.warning("Lyrics not found on the page.")
            # Try alternative selectors
            lyrics_divs = song_soup.find_all('div', class_=lambda x: x and 'kashi' in x.lower())
            if lyrics_divs:
                lyrics_div = lyrics_divs[0]
        
        if not lyrics_div:
            logger.warning("Lyrics not found on the page with alternative selectors either.")
            return None
        
        # Extract the lyrics text while preserving line breaks
        lyrics_lines = []
        for element in lyrics_div.descendants:
            if element.name == 'br':
                lyrics_lines.append('\n')
            elif isinstance(element, str) and element.strip():
                lyrics_lines.append(element.strip() + ' ')
        
        lyrics = ''.join(lyrics_lines).strip()
        
        # Alternative method: try to get text with line breaks preserved
        if not lyrics.strip():
            # If the above didn't work, try getting the text directly and then format it
            lyrics = lyrics_div.get_text()
            # Clean up the text
            lyrics = '\n'.join(line.strip() for line in lyrics.split('\n') if line.strip())
        
        if lyrics.strip():
            logger.info("Lyrics successfully extracted!")
            return lyrics
        else:
            logger.warning("Lyrics found but text extraction failed.")
            return None
            
    except requests.RequestException as e:
        logger.exception(f"Error during web request: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error during lyrics search: {e}")
        return None


def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Search for lyrics on uta-net.com using song name and artist.')
    parser.add_argument('file_path', nargs='?',
                        help='Path to the audio file to extract metadata from')
    parser.add_argument('--output', '-o', help='Output lyrics file path (default: output filename based on input)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=True)
    
    # Define the input file path
    input_file = args.file_path
    
    # Check if the input file exists
    if not os.path.exists(input_file):
        logger.exception(f"Input file does not exist: {input_file}")
        return
    
    logger.info(f"Extracting metadata from: {input_file}")
    
    # Extract metadata
    metadata = extract_metadata(input_file)
    
    # Print the extracted metadata
    logger.info("Extracted Metadata:")
    logger.info(f"Title: {metadata['title']}")
    logger.info(f"Artist: {metadata['artist']}")
    
    # Check if we have both title and artist
    if not metadata['title'] or not metadata['artist']:
        logger.warning("Missing title or artist information. Cannot search for lyrics.")
        return
    
    logger.info(f"\nSearching for lyrics for '{metadata['title']}' by {metadata['artist']}...")
    
    # Search for lyrics
    lyrics = search_uta_net(metadata['title'], metadata['artist'])
    
    if lyrics:
        logger.info(f"\nLyrics found for '{metadata['title']}' by {metadata['artist']}:")
        logger.info("-" * 50)
        logger.info(lyrics)
        logger.info("-" * 50)
        
        # Determine output file path
        output_file = args.output
        if not output_file:
            # Save lyrics to a file in the output directory
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            output_filename = f"{os.path.splitext(os.path.basename(input_file))[0]}_lyrics.txt"
            output_file = os.path.join(output_dir, output_filename)
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
            f.write("=" * 60 + "\n\n")
            f.write(lyrics)
            f.write(f"\n\nSource: uta-net.com")
        
        logger.info(f"\nLyrics saved to: {output_file}")
    else:
        logger.warning(f"\nCould not find lyrics for '{metadata['title']}' by {metadata['artist']}")


if __name__ == "__main__":
    main()