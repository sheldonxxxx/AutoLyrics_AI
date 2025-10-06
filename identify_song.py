#!/usr/bin/env python3
"""
Identify songs from ASR transcripts using LLM analysis and web search.

This module provides ASR-based song identification for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/identify_song.md

Key Features:
- LLM-powered song identification from ASR transcripts
- Web search integration (SearXNG metasearch engine)
- Retry mechanism with confidence scoring
- Result caching for performance optimization

Dependencies:
- pydantic_ai (structured LLM interactions)
- openai (API client library)
- requests (web search communication)

External Services:
- SearXNG metasearch engine (SEARXNG_URL)
- OpenAI-compatible API (OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL)

Pipeline Stage: 2/6 (Song Identification - Fallback)
"""

import os
import logging
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from pydantic import BaseModel, Field

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from logging_config import get_logger
from utils import get_openai_config, load_prompt_template

logger = get_logger(__name__)


def searxng_search(query: str) -> str:
    """
    Search the web using SearXNG metasearch engine.

    Args:
        query: The search query string

    Returns:
        Formatted search results as a string
    """
    searxng_url = os.getenv("SEARXNG_URL")
    if not searxng_url:
        error_msg = (
            "ERROR: SEARXNG_URL not found in environment variables. "
            "Please add SEARXNG_URL to your .env file, for example: "
            "SEARXNG_URL=http://localhost:8888"
        )
        logger.error(error_msg)
        return error_msg

    try:
        # SearXNG API parameters
        params = {
            'q': query,
            'format': 'json',
            'categories': 'general,music',
            'engines': 'google,bing,duckduckgo'
        }

        logger.info(f"Searching SearXNG at {searxng_url} with query: {query}")

        # Make request to SearXNG with proper error handling
        response = requests.get(
            f"{searxng_url}/search",
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        # Format results for LLM
        if 'results' in data and data['results']:
            results = []
            for result in data['results'][:10]:  # Limit to top 10 results
                title = result.get('title', '').strip()
                url = result.get('url', '').strip()
                content = result.get('content', '').strip()

                # Skip results with empty essential fields
                if not title or not url:
                    continue

                # Truncate content if too long
                if len(content) > 200:
                    content = content[:200] + '...'

                results.append({
                    'title': title,
                    'url': url,
                    'content': content
                })

            if not results:
                return f"No valid search results found for '{query}'"

            # Create a formatted string for the LLM
            formatted_results = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                formatted_results += f"{i}. **{result['title']}**\n"
                formatted_results += f"   URL: {result['url']}\n"
                if result['content']:
                    formatted_results += f"   Content: {result['content']}\n"
                formatted_results += "\n"

            return formatted_results.strip()
        else:
            return f"No search results found for '{query}'"

    except requests.exceptions.Timeout:
        logger.error(f"SearXNG search timed out for query: {query}")
        return f"Search request timed out for '{query}'"
    except requests.exceptions.RequestException as e:
        logger.error(f"SearXNG search request failed: {e}")
        return f"Search request failed: {str(e)}"
    except Exception as e:
        logger.error(f"SearXNG search error: {e}")
        return f"Search error: {str(e)}"


class SongIdentification(BaseModel):
    """Structured output for song identification results."""
    song_title: str = Field(description="The identified song title in its native language")
    artist_name: str = Field(description="The identified artist name in its native language")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    native_language: str = Field(description="The native language of the song (e.g., 'Japanese', 'English', 'Korean')")
    search_queries_used: List[str] = Field(description="List of search queries that were used")
    reasoning: str = Field(description="Explanation of how the identification was made")

class SongIdentifier:
    """Class to identify songs from ASR transcripts using LLM and web search."""

    def __init__(self):
        """Initialize the song identifier with LLM and search tools."""
        load_dotenv()

        # Get OpenAI configuration using utility function
        config = get_openai_config()

        # Create OpenAI provider with custom configuration
        openai_provider = OpenAIProvider(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"]
        )

        # Create OpenAI model with the provider
        openai_model = OpenAIChatModel(
            config["OPENAI_MODEL"],
            provider=openai_provider
        )

        # Create Pydantic AI agent with the model
        self.agent = Agent(
            openai_model,
            tools=[searxng_search],
            output_type=SongIdentification
        )

    def identify_song(self, transcript: str) -> Optional[SongIdentification]:
        """
        Identify song name and artist from ASR transcript.

        Args:
            transcript: ASR transcript of the song vocals

        Returns:
            Identified song information or None if identification fails
        """
        if not transcript or not transcript.strip():
            logger.error("Empty or invalid transcript provided")
            return None

        try:
            # Load prompt template from file
            prompt_template_path = os.path.join(
                os.path.dirname(__file__),
                "prompt",
                "song_identification_prompt.txt"
            )
            prompt_template = load_prompt_template(prompt_template_path)

            if not prompt_template:
                logger.error("Failed to load song identification prompt template")
                return None

            # Generate JSON schema from SongIdentification model
            json_schema = SongIdentification.model_json_schema()

            # Format the prompt with actual data and JSON schema
            user_prompt = prompt_template.format(
                transcript=transcript.strip()[:2000],  # Limit and clean input
                json_schema=json.dumps(json_schema, indent=2)
            )

            # Use Pydantic AI agent to run the identification
            logger.info("Running song identification with Pydantic AI agent")
            result = self.agent.run_sync(user_prompt)

            # Validate the result
            if not result or not result.output:
                logger.error("No result returned from Pydantic AI agent")
                return None

            if not isinstance(result.output, SongIdentification):
                logger.error(f"Invalid result type: {type(result.output)}")
                return None

            song_result = result.output

            # Validate required fields
            if not song_result.song_title or not song_result.artist_name:
                logger.warning("Missing song title or artist name in result")
                return None

            # Validate confidence score
            if not (0.0 <= song_result.confidence_score <= 1.0):
                logger.warning(f"Invalid confidence score: {song_result.confidence_score}")
                return None

            # Check confidence threshold
            if song_result.confidence_score > 0.3:
                logger.info(
                    f"Successfully identified song: '{song_result.song_title}' "
                    f"by '{song_result.artist_name}' "
                    f"({song_result.native_language}) - "
                    f"confidence: {song_result.confidence_score:.2f}"
                )
                return song_result
            else:
                logger.warning(
                    f"Low confidence identification: {song_result.confidence_score:.2f} "
                    f"for '{song_result.song_title}' by '{song_result.artist_name}'"
                )
                return None

        except Exception as e:
            logger.error(f"Error during song identification: {e}", exc_info=True)
            return None


def identify_song_from_asr_with_retry(transcript: str, result_file_path: Optional[str] = None, force_recompute: bool = False, max_retries: int = 3) -> Optional[Tuple[str, str, str]]:
    """
    Identify song from ASR transcript with retry mechanism and feedback about previous wrong results.

    Args:
        transcript (str): ASR transcript of the song vocals
        result_file_path (Optional[str]): Path to save/load identification results
        force_recompute (bool): If True, skip cache and always perform new identification
        max_retries (int): Maximum number of retry attempts (default: 3)

    Returns:
        Optional[Tuple[str, str, str]]: (song_title, artist_name, native_language) if identified, None otherwise
    """
    previous_attempts = []

    for attempt in range(max_retries):
        logger.info(f"Song identification attempt {attempt + 1}/{max_retries}")

        # Try to load existing result if file path provided and not forcing recompute
        if not force_recompute and result_file_path and Path(result_file_path).exists():
            try:
                with open(result_file_path, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)

                # Validate cached result has required fields
                if (cached_result.get('song_title') and
                    cached_result.get('artist_name') and
                    cached_result.get('confidence_score', 0) > 0.5):

                    logger.info(f"Loaded cached song identification: {cached_result['song_title']} by {cached_result['artist_name']}")
                    return (cached_result['song_title'],
                            cached_result['artist_name'],
                            cached_result.get('native_language', ''))

            except Exception as e:
                logger.warning(f"Failed to load cached song identification: {e}")

        # Perform new identification
        identifier = SongIdentifier()
        result = identifier.identify_song(transcript)

        if result and result.confidence_score > 0.5:
            song_info = (result.song_title, result.artist_name, result.native_language)

            # Check if this is a retry and we have previous attempts
            if attempt > 0 and previous_attempts:
                # For retries, we need to verify this isn't the same wrong result
                # For now, we'll assume different results are valid attempts
                # In a more sophisticated implementation, we could compare with previous wrong results
                pass

            # Save result if file path provided
            if result_file_path:
                try:
                    # Ensure directory exists
                    Path(result_file_path).parent.mkdir(parents=True, exist_ok=True)

                    # Save full result for future use
                    result_data = {
                        'song_title': result.song_title,
                        'artist_name': result.artist_name,
                        'confidence_score': result.confidence_score,
                        'search_queries_used': result.search_queries_used,
                        'reasoning': result.reasoning,
                        'attempt_number': attempt + 1,
                        'total_attempts': max_retries
                    }

                    with open(result_file_path, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)

                    logger.info(f"Saved song identification result to: {result_file_path}")

                except Exception as e:
                    logger.warning(f"Failed to save song identification result: {e}")

            logger.info(f"Successfully identified song on attempt {attempt + 1}: '{result.song_title}' by '{result.artist_name}'")
            return song_info
        else:
            if result:
                logger.warning(f"Low confidence identification on attempt {attempt + 1}: {result.confidence_score:.2f} for '{result.song_title}' by '{result.artist_name}'")
                previous_attempts.append({
                    'song_title': result.song_title,
                    'artist_name': result.artist_name,
                    'confidence': result.confidence_score,
                    'reasoning': result.reasoning
                })
            else:
                logger.warning(f"No identification result on attempt {attempt + 1}")

            # If this isn't the last attempt, continue to retry
            if attempt < max_retries - 1:
                logger.info(f"Retrying song identification (attempt {attempt + 2}/{max_retries})...")
                # Add a small delay between attempts
                import time
                time.sleep(1)
            else:
                logger.error(f"Failed to identify song after {max_retries} attempts")

    return None


def identify_song_from_asr(transcript: str, result_file_path: Optional[str] = None, force_recompute: bool = False) -> Optional[Tuple[str, str, str]]:
    """
    Convenience function to identify song from ASR transcript with optional caching.
    (Legacy function - use identify_song_from_asr_with_retry for new implementations)

    Args:
        transcript (str): ASR transcript of the song vocals
        result_file_path (Optional[str]): Path to save/load identification results
        force_recompute (bool): If True, skip cache and always perform new identification

    Returns:
        Optional[Tuple[str, str, str]]: (song_title, artist_name, native_language) if identified, None otherwise
    """
    # Try to load existing result if file path provided and not forcing recompute
    if not force_recompute and result_file_path and Path(result_file_path).exists():
        try:
            with open(result_file_path, 'r', encoding='utf-8') as f:
                cached_result = json.load(f)

            # Validate cached result has required fields
            if (cached_result.get('song_title') and
                cached_result.get('artist_name') and
                cached_result.get('confidence_score', 0) > 0.5):

                logger.info(f"Loaded cached song identification: {cached_result['song_title']} by {cached_result['artist_name']}")
                return (cached_result['song_title'],
                        cached_result['artist_name'],
                        cached_result.get('native_language', ''))

        except Exception as e:
            logger.warning(f"Failed to load cached song identification: {e}")

    # Perform new identification if no valid cached result
    identifier = SongIdentifier()
    result = identifier.identify_song(transcript)

    if result and result.confidence_score > 0.5:
        song_info = (result.song_title, result.artist_name, result.native_language)

        # Save result if file path provided
        if result_file_path:
            try:
                # Ensure directory exists
                Path(result_file_path).parent.mkdir(parents=True, exist_ok=True)

                # Save full result for future use
                result_data = {
                    'song_title': result.song_title,
                    'artist_name': result.artist_name,
                    'confidence_score': result.confidence_score,
                    'search_queries_used': result.search_queries_used,
                    'reasoning': result.reasoning
                }

                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                logger.info(f"Saved song identification result to: {result_file_path}")

            except Exception as e:
                logger.warning(f"Failed to save song identification result: {e}")

        return song_info
    else:
        return None


def main():
    """Test function for song identification."""
    import argparse

    parser = argparse.ArgumentParser(description='Identify song from ASR transcript')
    parser.add_argument('--transcript', '-t', help='ASR transcript text')
    parser.add_argument('--file', '-f', default="tmp/PRESERVED ROSES/PRESERVED ROSES_(Vocals)_UVR_MDXNET_Main_transcript.txt", help='File containing ASR transcript')
    parser.add_argument('--result-file', '-r', help='File to save/load song identification results')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)

    # Get transcript
    transcript = args.transcript
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                transcript = f.read()
        else:
            print(f"File not found: {args.file}")
            return 1

    if not transcript:
        print("No transcript provided. Use --transcript or --file")
        return 1

    print("Identifying song from transcript...")
    result_file = args.result_file if hasattr(args, 'result_file') else None
    result = identify_song_from_asr(transcript, result_file)

    if result:
        song_title, artist_name, native_language = result
        print(f"Identified: {song_title} by {artist_name} ({native_language})")
        return 0
    else:
        print("Could not identify song from transcript")
        return 1


if __name__ == "__main__":
    exit(main())