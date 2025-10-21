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

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerStdio
from pydantic_ai.models.instrumented import InstrumentationSettings
from dotenv import load_dotenv
from logging_config import get_logger
from utils import get_default_llm_config, load_prompt_template, SearxngLimitingToolset

logger = get_logger(__name__)


class SongStory(BaseModel):
    """Structured output for song background story results."""
    song_title: str = Field(description="The song title in its native language")
    artist_name: str = Field(description="The artist name in its native language")
    native_language: str = Field(description="The native language of the song")
    story_type: str = Field(description="Type of story found (e.g., 'anime_theme', 'tv_show_theme', 'creation_story')")
    story_summary: str = Field(description="Detailed summary of the song's creation story")
    background_story: Optional[str] = Field(default=None, description="If is a theme song, detailed description of the associated show/film")
    search_queries_used: List[str] = Field(description="List of search queries that were used")
    sources_used: List[str] = Field(description="List of sources/URLs used for the story")
    reasoning: str = Field(description="Explanation of how the story was identified and verified")


class SongStorySearcher:
    """Class to search for song background stories using LLM and web search."""

    def __init__(self, max_search_results: int = 5):
        """Initialize the song story searcher with LLM and remote MCP search tools.

        Args:
            max_search_results: Maximum number of search results to return (default: 5)
        """
        load_dotenv()

        # Get OpenAI configuration using utility function
        config = get_default_llm_config()

        # Create OpenAI provider with custom configuration
        openai_provider = OpenAIProvider(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"]
        )

        settings = ModelSettings(
            # max_tokens=5000,  # Avoid problematic long outputs
            extra_body={"enable_thinking": False}
        )

        # Create OpenAI model with the provider
        openai_model = OpenAIChatModel(
            config["OPENAI_MODEL"],
            provider=openai_provider,
            settings=settings
        )

        # Create MCP server connection - use environment variable or fallback to stdio
        mcp_searxng_server_url = os.getenv('MCP_SEARXNG_SERVER_URL')
        if mcp_searxng_server_url:
            logger.info(f"Using MCP server URL from environment: {mcp_searxng_server_url}")
            self.mcp_server = MCPServerStreamableHTTP(mcp_searxng_server_url)
        else:
            logger.info("MCP_SEARXNG_SERVER_URL not found, falling back to MCPServerStdio")
            SEARXNG_URL = os.getenv('SEARXNG_URL')
            if SEARXNG_URL:
                self.mcp_server = MCPServerStdio(
                    'npx', args=["-y", "mcp-searxng"],
                    env={
                        "SEARXNG_URL": SEARXNG_URL
                    }
                )
            else:
                logger.error("SEARXNG_URL environment variable is required when MCP_SEARXNG_SERVER_URL is not set")
                raise ValueError("SEARXNG_URL environment variable is required")

        # Wrap MCP server with result limiting toolset (configurable limit)
        self.limited_mcp_toolset = SearxngLimitingToolset(self.mcp_server, max_results=max_search_results)

        # Configure instrumentation settings to exclude binary content and sensitive data
        instrumentation_settings = InstrumentationSettings(
            include_binary_content=False,
            include_content=True
        )

        # Create Pydantic AI agent with wrapped MCP tools and instrumentation settings
        self.agent = Agent(
            openai_model,
            toolsets=[self.limited_mcp_toolset],
            output_type=SongStory,
            instrument=instrumentation_settings,
            retries=3
        )

    def search_song_story(self, song_title: str, artist_name: str, native_language: str) -> Optional[SongStory]:
        """
        Search for background story of a song using title, artist, and language information.

        Args:
            song_title: Title of the song
            artist_name: Name of the artist
            native_language: Native language of the song

        Returns:
            Song story information or None if search fails
        """
        if not song_title or not artist_name or not native_language:
            logger.error("Missing required parameters: song_title, artist_name, or native_language")
            return None

        try:
            # Load prompt template from file
            prompt_template_path = os.path.join(
                os.path.dirname(__file__),
                "prompt",
                "song_story_search_prompt.txt"
            )
            prompt_template = load_prompt_template(prompt_template_path)

            if not prompt_template:
                logger.exception("Failed to load song story search prompt template")
                return None

            # Generate JSON schema from SongStory model
            json_schema = SongStory.model_json_schema()

            # Format the prompt with song information and JSON schema
            user_prompt = prompt_template.format(
                song_title=song_title,
                artist_name=artist_name,
                native_language=native_language,
                json_schema=json.dumps(json_schema, indent=2)
            )
            logger.debug(f"Generated story search prompt length: {len(user_prompt)}")

            # Use Pydantic AI agent to run the story search with remote MCP server
            logger.info(f"Searching for background story of '{song_title}' by '{artist_name}'")
            result = self.agent.run_sync(user_prompt)
            logger.debug("Agent.run_sync() completed successfully for story search")

            if not result or not result.output:
                logger.exception("No result returned from Pydantic AI agent for story search")
                return None

            story_result = result.output
            logger.debug(f"Story result: {story_result}")

            # Validate required fields
            if not story_result.story_summary:
                logger.warning("Missing story summary in result")
                return None

            logger.info(
                f"Successfully found story for '{story_result.song_title}' "
                f"by '{story_result.artist_name}' "
                f"({story_result.story_type}) - "
            )
            return story_result

        except Exception as e:
            logger.exception(f"Error during song story search: {e}")
            return None


def search_song_story_from_identification(song_title: str, artist_name: str, native_language: str, paths: dict, force_recompute: bool = False, max_search_results: int = 5) -> Optional[Tuple[str, str, str, str, str, float]]:
    """
    Search for song background story with caching support.

    Args:
        song_title (str): Title of the song
        artist_name (str): Name of the artist
        native_language (str): Native language of the song
        paths (dict): Dictionary containing output file paths
        force_recompute (bool): If True, skip cache and always perform new search

    Returns:
        Optional[Tuple]: (story_type, story_summary, story_details, sources_used, reasoning, confidence_score) if found, None otherwise
    """
    result_file_path = str(paths.get('song_story', 'song_story_result.json'))

    # Try to load existing result if file path provided and not forcing recompute
    if not force_recompute and result_file_path and Path(result_file_path).exists():
        try:
            with open(result_file_path, 'r', encoding='utf-8') as f:
                cached_result = json.load(f)

            # Validate cached result has required fields
            if (cached_result.get('story_summary')):

                logger.info(f"Loaded cached song story: {cached_result.get('story_type', 'Unknown')} for {song_title}")
                return (cached_result.get('story_type', ''),
                        cached_result.get('story_summary', ''),
                        cached_result.get('background_story', ''),
                        cached_result.get('sources_used', []),
                        cached_result.get('reasoning', ''))

        except Exception as e:
            logger.warning(f"Failed to load cached song story: {e}")

    # Perform new story search
    searcher = SongStorySearcher(max_search_results)
    result = searcher.search_song_story(song_title, artist_name, native_language)

    if result:
        story_info = (result.story_type, result.story_summary,
                     result.sources_used, result.reasoning)

        # Save result if file path provided
        if result_file_path:
            try:
                # Ensure directory exists
                Path(result_file_path).parent.mkdir(parents=True, exist_ok=True)

                # Save full result for future use
                result_data = {
                    'song_title': result.song_title,
                    'artist_name': result.artist_name,
                    'native_language': result.native_language,
                    'story_type': result.story_type,
                    'story_summary': result.story_summary,
                    'background_story': result.background_story,
                    'search_queries_used': result.search_queries_used,
                    'sources_used': result.sources_used,
                    'reasoning': result.reasoning
                }

                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                logger.info(f"Saved song story result to: {result_file_path}")

            except Exception as e:
                logger.warning(f"Failed to save song story result: {e}")

        logger.info(f"Successfully found story for '{result.song_title}' by '{result.artist_name}': {result.story_type}")
        return story_info
    else:
        logger.warning(f"No story search result for '{song_title}' by '{artist_name}'")

    return None


def main():
    """Test function for song story search."""
    import argparse

    parser = argparse.ArgumentParser(description='Search for song background story')
    parser.add_argument('--title', '-t', required=True, help='Song title')
    parser.add_argument('--artist', '-a', required=True, help='Artist name')
    parser.add_argument('--language', '-l', required=True, help='Native language of the song')
    parser.add_argument('--result-file', '-r', help='File to save/load song story results')
    parser.add_argument('--max-search-results', type=int, default=5,
                            help='Maximum number of search results to return (default: 5)')
    parser.add_argument('--log-level', default='INFO',
                            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                            help='Logging level (default: INFO)')
    parser.add_argument('--logfire', action='store_true',
                          help='Enable Logfire integration')

    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    from logging_config import setup_logging
    setup_logging(level=log_level, enable_logfire=args.logfire)

    print(f"Searching for background story of '{args.title}' by '{args.artist}'...")

    # Get max search results from command line arg or environment variable
    max_search_results = args.max_search_results
    if max_search_results == 5:  # If using default, check environment variable
        max_search_results = int(os.getenv('MAX_SEARCH_RESULTS', '5'))

    paths = {
        'song_story': args.result_file if args.result_file else "song_story_result.json",
    }
    result = search_song_story_from_identification(args.title, args.artist, args.language, paths, max_search_results=max_search_results)

    if result:
        story_type, story_summary, story_details, background_story, sources_used, reasoning = result
        print(f"Story Type: {story_type}")
        print(f"Summary: {story_summary}")
        print(f"Background Story: {background_story}")
        print(f"Details: {story_details}")
        if sources_used:
            print(f"Sources: {', '.join(sources_used)}")
        return 0
    else:
        print("Could not find background story for the song")
        return 1


if __name__ == "__main__":
    result = main()
    exit(result)