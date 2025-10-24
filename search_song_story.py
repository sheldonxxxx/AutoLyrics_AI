#!/usr/bin/env python3
"""
Search for song background stories and context information.

This module searches for detailed background information about songs, including:
- Anime/TV show theme song context
- Story behind the song creation
- Cultural or historical significance
- Artist background related to the song
- Any other relevant contextual information

For comprehensive documentation, see: docs/modules/search_song_story.md

Key Features:
- LLM-powered story search using song title and artist
- Remote MCP server integration (SearXNG metasearch engine)
- Native language search support
- Structured output with confidence scoring
- Result caching for performance optimization

Dependencies:
- pydantic_ai (structured LLM interactions)
- openai (API client library)

External Services:
- Remote MCP SearXNG server
- OpenAI-compatible API (OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL)

Pipeline Stage: 2.5/6 (Story Search - After Song Identification)
"""

import os
import logging
import json
from typing import List, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field

from logging_config import get_logger, setup_logging
from utils import get_default_llm_config, load_prompt_template, get_base_argparser
from agent_utils import prepare_agent, SearxngLimitingToolset, get_searxng_mcp

logger = get_logger(__name__)


class SongStory(BaseModel):
    """Structured output for song background story results."""

    song_title: str = Field(description="The song title in its native language")
    artist_name: str = Field(description="The artist name in its native language")
    native_language: str = Field(description="The native language of the song")
    story_type: str = Field(
        description="Base story of this song (e.g., 'anime', 'tv_show', 'movie'), empty if none"
    )
    creation_story: str = Field(
        description="Detailed summary of the song's creation story"
    )
    background_story: Optional[str] = Field(
        default=None,
        description="If is a theme song, detailed description of the associated show/film",
    )
    search_queries_used: List[str] = Field(
        description="List of search queries that were used"
    )
    sources_used: List[str] = Field(
        description="List of sources/URLs used for the story"
    )
    reasoning: str = Field(
        description="Explanation of how the story was identified and verified, in English"
    )


def init_agent(system_prompt: str, max_search_results: int = 5):
    """Initialize the song story searcher with LLM and remote MCP search tools.

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
        output_type=SongStory,
        modelsettings_kwargs={
            "extra_body": {
                "enable_thinking": False,  # For Qwen
                # "reasoning": {"enabled": False} # For xAI Grok
            }
        },
    )


def search_song_story(
    song_title: str,
    artist_name: str,
    native_language: str,
    paths: dict,
    recompute: bool = False,
    max_search_results: int = 5,
) -> bool:
    """
    Search for song background story with caching support.

    Args:
        song_title (str): Title of the song
        artist_name (str): Name of the artist
        native_language (str): Native language of the song
        paths (dict): Dictionary containing output file paths
        force_recompute (bool): If True, skip cache and always perform new search

    Returns:
        Optional[Tuple]: (story_type, creation_story, story_details, sources_used, reasoning) if found, None otherwise
    """
    result_file_path = paths['song_story']

    # Try to load existing result if file path provided and not forcing recompute
    if not recompute and result_file_path and Path(result_file_path).exists():
        logger.info(f"Song story result file found at: {result_file_path}, skipping search")
        return True

    if not song_title or not artist_name:
        logger.error("Missing required parameters: song_title, artist_name")
        return False

    try:
        user_prompt = f"song_title: {song_title}\nartist_name: {artist_name}\nnative_language: {native_language}\n"

        logger.info(f"Searching for background story of '{song_title}' by '{artist_name}'")

        agent = init_agent(
            load_prompt_template("song_story_search_prompt.txt"),
            max_search_results=max_search_results,
        )

        result = agent.run_sync(user_prompt)

        logger.debug("Agent.run_sync() completed successfully for story search")

        if not result or not result.output:
            logger.error("No result returned from Pydantic AI agent for story search")
            return False

        story_result = result.output
        logger.debug(f"Story result: {story_result}")

        logger.info(
            f"Successfully found story for '{story_result.song_title}' "
            f"by '{story_result.artist_name}' "
            f"({story_result.story_type}) - "
        )

    except Exception:
        logger.exception("Error during song story search")
        return False

    try:

        # Save full result for future use - dynamically create from SongStory model
        result_data = result.output.model_dump(mode="json")

        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved song story result to: {result_file_path}")

    except Exception:
        logger.exception("Failed to save song story result")
        return False

    return True


def main():
    """Test function for song story search."""
    import dotenv

    dotenv.load_dotenv()

    parser = get_base_argparser(
        description="Search for song background story", search=True
    )

    parser.add_argument("--title", "-t", required=True, help="Song title")
    parser.add_argument("--artist", "-a", required=True, help="Artist name")
    parser.add_argument(
        "--language", "-l", required=True, help="Native language of the song"
    )
    parser.add_argument(
        "--result-file", "-r", help="File to save/load song story results"
    )

    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    logger.info(
        f"Searching for background story of '{args.title}' by '{args.artist}'..."
    )

    # Get max search results from command line arg or environment variable
    max_search_results = args.max_search_results
    if max_search_results == 5:  # If using default, check environment variable
        max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
        
    output_path = Path(args.result_file) if args.result_file else Path("song_story_result.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paths = {
        "song_story": output_path,
    }
    
    search_song_story(
        args.title,
        args.artist,
        args.language,
        paths,
        max_search_results=max_search_results,
        recompute=args.recompute,
    )


if __name__ == "__main__":
    main()
