#!/usr/bin/env python3
"""
Identify songs from ASR transcripts using LLM analysis and web search.

This module provides ASR-based song identification for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/identify_song.md

Key Features:
- LLM-powered song identification from ASR transcripts
- Remote MCP server integration (SearXNG metasearch engine)
- Retry mechanism with confidence scoring
- Result caching for performance optimization

Dependencies:
- pydantic_ai (structured LLM interactions)
- openai (API client library)

External Services:
- Remote MCP SearXNG server
- OpenAI-compatible API (OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL)

Pipeline Stage: 2/6 (Song Identification - Fallback)
"""

import os
import logging
import json
from typing import List, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field

from pydantic_ai import Agent
from logging_config import get_logger, setup_logging
from utils import (
    get_base_argparser,
    get_default_llm_config,
    load_prompt_template,
    remove_timestamps_from_transcript,
)
from agent_utils import (
    SearxngLimitingToolset,
    get_searxng_mcp,
    prepare_agent,
)

logger = get_logger(__name__)


class SongIdentification(BaseModel):
    """Structured output for song identification results."""

    song_title: str = Field(
        description="The identified song title in its native language"
    )
    artist_name: str = Field(
        description="The identified artist name in its native language"
    )
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    native_language: str = Field(
        description="The native language of the song (e.g., 'Japanese', 'English', 'Korean')"
    )
    lyrics_content: Optional[str] = Field(
        description="The complete lyrics content if found, None otherwise"
    )
    lyrics_source_url: Optional[str] = Field(
        description="The URL where the lyrics were obtained from, if found"
    )
    search_queries_used: List[str] = Field(
        description="List of search queries that were used"
    )
    reasoning: str = Field(description="Explanation of how the identification was made")


def init_agent(system_prompt: str, max_search_results: int = 5) -> Agent:
    """Initialize the song identifier with LLM and remote MCP search tools.

    Args:
        max_search_results: Maximum number of search results to return (default: 5)
    """
    # Get OpenAI configuration using utility function
    config = get_default_llm_config()

    # Wrap MCP server with result limiting toolset (configurable limit)
    limited_mcp_toolset = SearxngLimitingToolset(
        get_searxng_mcp(), max_results=max_search_results
    )

    return prepare_agent(
        config["OPENAI_BASE_URL"],
        config["OPENAI_API_KEY"],
        config["OPENAI_MODEL"],
        instructions=system_prompt,
        toolsets=[limited_mcp_toolset],
        output_type=SongIdentification,
        modelsettings_kwargs={
            "extra_body": {
                "enable_thinking": False,  # For Qwen
                # "reasoning": {"enabled": False} # For xAI Grok
            }
        },
    )


def identify_song(
    transcript: str, metadata: Optional[dict] = None, max_search_results: int = 5
) -> Optional[SongIdentification]:
    """
    Identify song and search for lyrics using both metadata and ASR transcript.

    Args:
        transcript: ASR transcript of the song vocals
        metadata: Dictionary containing song metadata (title, artist, album, etc.)

    Returns:
        Identified song information with lyrics if found
    """
    if not transcript or not transcript.strip():
        logger.exception("Empty or invalid transcript provided")
        return None

    try:
        # Remove timestamps from transcript to reduce token usage
        cleaned_transcript = remove_timestamps_from_transcript(transcript)

        # If no metadata provided, use transcript-only identification
        if not metadata:
            system_prompt = load_prompt_template("song_identification_prompt.txt")
            user_prompt = cleaned_transcript
        else:
            system_prompt = load_prompt_template(
                "song_identification_with_metadata_prompt.txt"
            )
            user_prompt = f"Title: {metadata.get('title', '')}\nArtist: {metadata.get('artist', '')}\nAlbum: {metadata.get('album', '')}\n\nTranscript:\n{cleaned_transcript}"

        if not system_prompt:
            logger.exception("Failed to load song identification system prompt")
            return None

        agent = init_agent(system_prompt, max_search_results=max_search_results)

        # Use Pydantic AI agent to run the identification with remote MCP server
        logger.info(
            "Running song identification with metadata using Pydantic AI agent and MCP server"
        )
        result = agent.run_sync(user_prompt)
        logger.debug("Agent.run_sync() completed successfully for metadata scenario")

        if not result or not result.output:
            logger.exception(
                "No result returned from Pydantic AI agent for metadata scenario"
            )
            logger.exception(f"Result: {result}")
            return None

        song_result = result.output
        logger.debug(f"Song result with metadata: {song_result}")

        # Validate required fields
        if not song_result.song_title or not song_result.artist_name:
            logger.warning("Missing song title or artist name in metadata result")
            logger.warning(
                f"song_title: '{song_result.song_title}', artist_name: '{song_result.artist_name}'"
            )
            return None

        # Validate confidence score
        if not (0.0 <= song_result.confidence_score <= 1.0):
            logger.warning(f"Invalid confidence score: {song_result.confidence_score}")
            return None

        # Check confidence threshold
        if song_result.confidence_score > 0.7:
            return song_result
        else:
            logger.warning(
                f"Low confidence identification with metadata: {song_result.confidence_score:.2f} "
                f"for '{song_result.song_title}' by '{song_result.artist_name}'"
            )
            return None

    except Exception as e:
        logger.exception(f"Error during song identification with metadata: {e}")
        return None


def identify_song_from_asr(
    transcript: str,
    paths: dict,
    force_recompute: bool = False,
    max_search_results: int = 5,
    metadata: Optional[dict] = None,
) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
    """
    Identify song from ASR transcript with retry mechanism and feedback about previous wrong results.

    Args:
        transcript (str): ASR transcript of the song vocals
        result_file_path (Optional[str]): Path to save/load identification results
        force_recompute (bool): If True, skip cache and always perform new identification

    Returns:
        Optional[Tuple[str, str, str, bool, Optional[str], Optional[str]]]: (song_title, artist_name, native_language, lyrics_content, lyrics_source_url) if identified, None otherwise
    """
    result_file_path = str(paths["song_identification"])
    lyrics_file_path = str(
        paths.get("lyrics_file", result_file_path.replace(".json", "_lyrics.txt"))
    )

    # Try to load existing result if file path provided and not forcing recompute
    if not force_recompute and Path(result_file_path).exists():
        try:
            with open(result_file_path, "r", encoding="utf-8") as f:
                cached_result = json.load(f)

            if cached_result:
                logger.info(f"Trying to load cached song identification from: {result_file_path}")
                result = SongIdentification(**cached_result)

                logger.info(
                    f"Loaded cached song identification: {result.song_title} by {result.artist_name}"
                )
                
                logger.debug(f"Cached result loaded: {result}")

                return (
                    result.song_title,
                    result.artist_name,
                    result.native_language,
                    result.lyrics_content,
                    result.lyrics_source_url,
                )

        except Exception as e:
            logger.warning(f"Failed to load cached song identification: {e}")

    # Perform new identification
    result = identify_song(
        transcript, metadata=metadata, max_search_results=max_search_results
    )

    if result and result.confidence_score > 0.7:

        song_info = (
            result.song_title,
            result.artist_name,
            result.native_language,
            result.lyrics_content,
            result.lyrics_source_url,
        )

        # Save result if file path provided
        if result_file_path:
            try:
                # Ensure directory exists
                Path(result_file_path).parent.mkdir(parents=True, exist_ok=True)

                # Save full result for future use
                result_data = result.model_dump(mode="json")

                with open(result_file_path, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                logger.info(f"Saved song identification result to: {result_file_path}")

                # Save lyrics to separate file if found
                if result.lyrics_content:
                    try:
                        with open(lyrics_file_path, "w", encoding="utf-8") as f:
                            f.write(result.lyrics_content)
                        logger.info(f"Saved lyrics to: {lyrics_file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save lyrics file: {e}")

            except Exception as e:
                logger.warning(f"Failed to save song identification result: {e}")

        logger.info(
            f"Successfully identified song: '{result.song_title}' by '{result.artist_name}' (lyrics: {'found' if result.lyrics_content else 'not found'})"
        )
        return song_info
    else:
        if result:
            logger.warning(
                f"Low confidence identification: {result.confidence_score:.2f} for '{result.song_title}' by '{result.artist_name}'"
            )
        else:
            logger.warning(f"No identification result")

    return None


def main():
    """Test function for song identification."""
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    parser = get_base_argparser(
        description="Identify song from ASR transcript", search=True
    )

    parser.add_argument(
        "--file", "-f", required=True, help="File containing ASR transcript"
    )
    parser.add_argument("--title", "-t", help="Song title metadata")
    parser.add_argument("--artist", "-a", help="Artist name metadata")
    parser.add_argument("--album", "-A", help="Album name metadata")
    parser.add_argument(
        "--result-file", "-r", help="File to save/load song identification results"
    )

    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    if os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            transcript = f.read()
    else:
        print(f"File not found: {args.file}")
        return 1

    if not transcript:
        print("No transcript provided. Use --transcript or --file")
        return 1

    print("Identifying song from transcript...")

    # Get max search results from command line arg or environment variable
    max_search_results = args.max_search_results
    if max_search_results == 5:  # If using default, check environment variable
        max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

    paths = {
        "song_identification": (
            args.result_file if args.result_file else "song_identification_result.json"
        ),
    }

    # Prepare metadata dictionary if any metadata provided
    metadata = {}
    if args.title:
        metadata["title"] = args.title
    if args.artist:
        metadata["artist"] = args.artist
    if args.album:
        metadata["album"] = args.album

    result = identify_song_from_asr(
        transcript, paths, metadata=metadata, max_search_results=max_search_results
    )

    if result:
        song_title, artist_name, native_language, lyrics_content, lyrics_source_url = (
            result
        )
        print(f"Identified: {song_title} by {artist_name} ({native_language})")
        if lyrics_content:
            print(f"Lyrics file saved")
            if lyrics_source_url:
                print(f"Lyrics source: {lyrics_source_url}")
        else:
            print("No lyrics found")
        return 0
    else:
        print("Could not identify song from transcript")
        return 1


if __name__ == "__main__":
    result = main()
    exit(result)
