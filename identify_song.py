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
from utils import (
    get_logger,
    setup_logging,
    read_file,
    get_base_argparser,
    get_default_llm_config,
    load_prompt_template,
    remove_timestamps_from_transcript,
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
    confidence_score: float = Field(description="Confidence score", ge=0.0, le=1.0)
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


def init_agent(system_prompt: str, max_search_results: int = 15) -> Agent:
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


def _load_existing_result(paths: dict, recompute: bool) -> bool:
    """Load existing song identification result if available and not recomputing."""
    result_file_path = paths["song_identification"]
    if not recompute and result_file_path.exists():
        try:
            logger.info(f"Song identification result file found, skipping recompute: {result_file_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load cached song identification: {e}")
    return False


def _run_identification(
    transcript: str,
    metadata: Optional[dict],
    max_search_results: int,
) -> Optional[SongIdentification]:
    """Run the song identification process using LLM and return the result."""
    if not transcript or not transcript.strip():
        logger.error("Empty or invalid transcript provided")
        return None

    try:
        # Remove timestamps from transcript to reduce token usage
        cleaned_transcript = remove_timestamps_from_transcript(transcript)

        # Prepare prompts based on metadata availability
        if not metadata:
            system_prompt = load_prompt_template("song_identification_prompt.txt")
            user_prompt = cleaned_transcript
        else:
            system_prompt = load_prompt_template("song_identification_with_metadata_prompt.txt")
            user_prompt = (
                f"Title: {metadata.get('title', '')}\n"
                f"Artist: {metadata.get('artist', '')}\n"
                f"Album: {metadata.get('album', '')}\n\n"
                f"Transcript:\n{cleaned_transcript}"
            )

        if not system_prompt:
            logger.error("Failed to load song identification system prompt")
            return None

        agent = init_agent(system_prompt, max_search_results=max_search_results)

        # Run identification
        logger.info("Running song identification using Pydantic AI agent and MCP server")
        result = agent.run_sync(user_prompt)
        logger.debug("Agent.run_sync() completed successfully")

        if not result or not result.output:
            logger.error("No result returned from Pydantic AI agent")
            return None

        song_result = result.output
        logger.debug(f"Song result: {song_result}")

        # Validate required fields
        if not song_result.song_title or not song_result.artist_name:
            logger.warning("Missing song title or artist name in result")
            logger.warning(f"song_title: '{song_result.song_title}', artist_name: '{song_result.artist_name}'")
            return None

        return song_result

    except Exception as e:
        logger.exception(f"Error during song identification: {e}")
        return None


def _save_result(song_result: SongIdentification, paths: dict) -> bool:
    """Save the song identification result and lyrics to files."""
    result_file_path = paths["song_identification"]
    lyrics_file_path = paths["lyrics_txt"]

    try:
        # Save full result for future use
        result_data = song_result.model_dump(mode="json")
        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved song identification result to: {result_file_path}")

        # Save lyrics to separate file if found
        if song_result.lyrics_content:
            with open(lyrics_file_path, "w", encoding="utf-8") as f:
                f.write(song_result.lyrics_content)
            logger.info(f"Saved lyrics to: {lyrics_file_path}")

        return True
    except Exception as e:
        logger.exception(f"Failed to save song identification result: {e}")
        return False


def _log_low_confidence(song_result: Optional[SongIdentification]) -> None:
    """Log low confidence identification results."""
    if song_result:
        logger.warning(
            f"Low confidence identification: {song_result.confidence_score:.2f} "
            f"for '{song_result.song_title}' by '{song_result.artist_name}'"
        )
    else:
        logger.warning("No identification result")

def identify_song_from_asr(
    transcript: str,
    paths: dict,
    metadata: Optional[dict] = None,
    recompute: bool = False,
    max_search_results: int = 15,
) -> bool:
    """
    Identify song from ASR transcript with retry mechanism and feedback about previous wrong results.

    Args:
        transcript (str): ASR transcript text
        paths (dict): Dictionary containing file paths:
            - "song_identification": Path to save/load song identification results
            - "lyrics_txt": Path to save identified lyrics content
        metadata (dict, optional): Optional metadata to assist identification:
            - "title": Song title
            - "artist": Artist name
            - "album": Album name
        recompute (bool): If True, forces re-identification even if output exists
        max_search_results (int): Maximum number of search results to consider

    Returns:
        bool: True if song identification succeeded, False otherwise
    """
    if _load_existing_result(paths, recompute):
        return True

    song_result = _run_identification(transcript, metadata, max_search_results)
    if not song_result:
        return False

    if song_result.confidence_score > 0.7:
        if _save_result(song_result, paths):
            logger.info(
                f"Successfully identified song: '{song_result.song_title}' by '{song_result.artist_name}' (lyrics: {'found' if song_result.lyrics_content else 'not found'})"
            )
            return True
        else:
            return False
    else:
        _log_low_confidence(song_result)
        return False

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

    asr_transcript_path = Path(args.file)
    if not asr_transcript_path.exists():
        logger.error(f"ASR transcript file does not exist: {asr_transcript_path}")
        return

    print("Identifying song from transcript...")

    # Get max search results from command line arg or environment variable
    max_search_results = args.max_search_results
    if max_search_results == 5:  # If using default, check environment variable
        max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

    if args.result_file:
        result_file_path = Path(args.result_file)
        lyrics_file_path = Path(result_file_path.stem + "_lyrics.txt")
        Path(result_file_path.parent).mkdir(parents=True, exist_ok=True)
    else:
        result_file_path = Path("song_identification_result.json")
        lyrics_file_path = Path("song_identification_lyrics.txt")

    paths = {
        "song_identification": result_file_path,
        "lyrics_txt": lyrics_file_path,
    }

    # Prepare metadata dictionary if any metadata provided
    metadata = {
        "title": args.title if args.title else "",
        "artist": args.artist if args.artist else "",
        "album": args.album if args.album else "",
    }
    
    asr_transcript = read_file(asr_transcript_path)

    identify_song_from_asr(
        asr_transcript, paths, metadata=metadata, max_search_results=max_search_results
    )


if __name__ == "__main__":
    main()
