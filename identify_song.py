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
import re
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from pydantic import BaseModel, Field

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerStdio
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.toolsets import WrapperToolset
from dotenv import load_dotenv
from logging_config import get_logger
from utils import get_default_llm_config, load_prompt_template, remove_timestamps_from_transcript, extract_lyrics

logger = get_logger(__name__)

class SearxngLimitingToolset(WrapperToolset):
    """Custom wrapper toolset to limit SearXNG search results."""

    def __init__(self, wrapped, max_results: int = 5):
        """Initialize with configurable result limit.

        Args:
            wrapped: The underlying toolset to wrap
            max_results: Maximum number of search results to return (default: 5)
        """
        super().__init__(wrapped)
        self.max_results = max_results

    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx, tool) -> Any:
        """Intercept tool calls and limit SearXNG results."""
        # Call the original tool first
        result = await super().call_tool(name, tool_args, ctx, tool)

        # If this is a SearXNG search tool, limit results
        if name == "searxng_web_search":
            result_list = result.split('\n\n')
            logger.info(f"Limiting SearXNG results from {len(result_list)} to {self.max_results}")
            # Return only the first max_results results
            return '\n\n'.join(result_list[:self.max_results])
        elif name == "web_url_read":
            result = extract_lyrics(result)

        return result


class SongIdentification(BaseModel):
    """Structured output for song identification results."""
    song_title: str = Field(description="The identified song title in its native language")
    artist_name: str = Field(description="The identified artist name in its native language")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    native_language: str = Field(description="The native language of the song (e.g., 'Japanese', 'English', 'Korean')")
    search_queries_used: List[str] = Field(description="List of search queries that were used")
    reasoning: str = Field(description="Explanation of how the identification was made")
    lyrics_content: Optional[str] = Field(description="The complete lyrics content if found, None otherwise")
    lyrics_source_url: Optional[str] = Field(description="The URL where the lyrics were obtained from, if found")
class SongIdentifier:
    """Class to identify songs from ASR transcripts using LLM and web search."""

    def __init__(self, max_search_results: int = 5):
        """Initialize the song identifier with LLM and remote MCP search tools.

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
            max_tokens=5000, # Avoid problematic long outputs
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
            output_type=SongIdentification,
            instrument=instrumentation_settings,
            retries=3
        )

    def identify_song(self, transcript: str) -> Optional[SongIdentification]:
        """
        Identify song name and artist from ASR transcript using remote MCP server.

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
                logger.exception("Failed to load song identification prompt template")
                return None

            # Generate JSON schema from SongIdentification model
            json_schema = SongIdentification.model_json_schema()

            # Remove timestamps from transcript to reduce token usage
            cleaned_transcript = remove_timestamps_from_transcript(transcript)

            # Format the prompt with cleaned transcript and JSON schema
            user_prompt = prompt_template.format(
                transcript=cleaned_transcript,  # Limit and clean input
                json_schema=json.dumps(json_schema, indent=2)
            )
            logger.debug(f"Generated prompt length: {len(user_prompt)}")

            # Use Pydantic AI agent to run the identification with remote MCP server
            logger.info("Running song identification with Pydantic AI agent and remote MCP server")
            result = self.agent.run_sync(user_prompt)
            logger.debug("Agent.run_sync() completed successfully")

            if not result or not result.output:
                logger.exception("No result returned from Pydantic AI agent")
                return None

            song_result = result.output
            logger.debug(f"Song result: {song_result}")

            # Validate required fields
            if not song_result.song_title or not song_result.artist_name:
                logger.warning("Missing song title or artist name in result")
                logger.warning(f"song_title: '{song_result.song_title}', artist_name: '{song_result.artist_name}'")
                return None

            # Validate confidence score
            if not (0.0 <= song_result.confidence_score <= 1.0):
                logger.warning(f"Invalid confidence score: {song_result.confidence_score}")
                return None

            # Check confidence threshold
            if song_result.confidence_score > 0.7:
                logger.info(
                    f"Successfully identified song: '{song_result.song_title}' "
                    f"by '{song_result.artist_name}' "
                    f"({song_result.native_language}) - "
                    f"confidence: {song_result.confidence_score:.2f}"
                )
                if not song_result.lyrics_content:
                    logger.info("No lyrics found in result")

                return song_result
            else:
                logger.warning(
                    f"Low confidence identification: {song_result.confidence_score:.2f} "
                    f"for '{song_result.song_title}' by '{song_result.artist_name}'"
                )
                return None

        except Exception as e:
            logger.exception(f"Error during song identification: {e}")
            return None

    def identify_song_with_metadata(self, transcript: str, metadata: dict) -> Optional[SongIdentification]:
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

        if not metadata or not metadata.get('title') or not metadata.get('artist'):
            logger.exception("Invalid metadata provided")
            return None

        try:
            # Load metadata-specific prompt template from file
            prompt_template_path = os.path.join(
                os.path.dirname(__file__),
                "prompt",
                "song_identification_with_metadata_prompt.txt"
            )
            prompt_template = load_prompt_template(prompt_template_path)

            if not prompt_template:
                logger.exception("Failed to load song identification with metadata prompt template")
                return None

            # Generate JSON schema from SongIdentification model
            json_schema = SongIdentification.model_json_schema()

            # Remove timestamps from transcript to reduce token usage
            cleaned_transcript = remove_timestamps_from_transcript(transcript)

            # Format the prompt with metadata, cleaned transcript and JSON schema
            user_prompt = prompt_template.format(
                title=metadata.get('title', ''),
                artist=metadata.get('artist', ''),
                album=metadata.get('album', ''),
                transcript=cleaned_transcript[:2000],  # Limit and clean input
                json_schema=json.dumps(json_schema, indent=2)
            )
            logger.debug(f"Generated metadata prompt length: {len(user_prompt)}")

            # Use Pydantic AI agent to run the identification with remote MCP server
            logger.info("Running song identification with metadata using Pydantic AI agent and MCP server")
            result = self.agent.run_sync(user_prompt)
            logger.debug("Agent.run_sync() completed successfully for metadata scenario")

            if not result or not result.output:
                logger.exception("No result returned from Pydantic AI agent for metadata scenario")
                logger.exception(f"Result: {result}")
                return None

            song_result = result.output
            logger.debug(f"Song result with metadata: {song_result}")

            # Check if ASR content is weird/unrelated first
            if getattr(song_result, 'reject_asr_content', False):
                logger.warning("ASR content was rejected - skipping song identification")
                return None

            # Validate required fields
            if not song_result.song_title or not song_result.artist_name:
                logger.warning("Missing song title or artist name in metadata result")
                logger.warning(f"song_title: '{song_result.song_title}', artist_name: '{song_result.artist_name}'")
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


def identify_song_from_asr(transcript: str, paths: Path, force_recompute: bool = False, max_search_results: int = 5, metadata: Optional[dict] = None) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
    """
    Identify song from ASR transcript with retry mechanism and feedback about previous wrong results.

    Args:
        transcript (str): ASR transcript of the song vocals
        result_file_path (Optional[str]): Path to save/load identification results
        force_recompute (bool): If True, skip cache and always perform new identification

    Returns:
        Optional[Tuple[str, str, str, bool, Optional[str], Optional[str]]]: (song_title, artist_name, native_language, lyrics_content, lyrics_source_url) if identified, None otherwise
    """
    result_file_path = str(paths['song_identification'])
    lyrics_file_path = str(paths.get('lyrics_file', result_file_path.replace('.json', '_lyrics.txt')))

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
                        cached_result.get('native_language', ''),
                        cached_result.get('lyrics_content', ""),
                        cached_result.get('lyrics_source_url', ""))

        except Exception as e:
            logger.warning(f"Failed to load cached song identification: {e}")

    # Perform new identification
    identifier = SongIdentifier(max_search_results)
    if metadata is not None:
        result = identifier.identify_song_with_metadata(transcript, metadata)
    else:
        result = identifier.identify_song(transcript)

    if result and result.confidence_score > 0.7:
        song_info = (result.song_title, result.artist_name, result.native_language, result.lyrics_content, result.lyrics_source_url)

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
                    'lyrics_content': result.lyrics_content,
                    'lyrics_source_url': result.lyrics_source_url,
                    'native_language': result.native_language
                }

                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                logger.info(f"Saved song identification result to: {result_file_path}")

                # Save lyrics to separate file if found
                if result.lyrics_content:
                    try:
                        with open(lyrics_file_path, 'w', encoding='utf-8') as f:
                            f.write(result.lyrics_content)
                        logger.info(f"Saved lyrics to: {lyrics_file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save lyrics file: {e}")

            except Exception as e:
                logger.warning(f"Failed to save song identification result: {e}")

        logger.info(f"Successfully identified song: '{result.song_title}' by '{result.artist_name}' (lyrics: {'found' if result.lyrics_content else 'not found'})")
        return song_info
    else:
        if result:
            logger.warning(f"Low confidence identification: {result.confidence_score:.2f} for '{result.song_title}' by '{result.artist_name}'")
        else:
            logger.warning(f"No identification result")

    return None

def main():
    """Test function for song identification."""
    import argparse

    parser = argparse.ArgumentParser(description='Identify song from ASR transcript')
    parser.add_argument('--transcript', '-t', help='ASR transcript text')
    parser.add_argument('--file', '-f', default="tmp/0017606481/0017606481_transcript.txt", help='File containing ASR transcript')
    parser.add_argument('--result-file', '-r', help='File to save/load song identification results')
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

    # Get max search results from command line arg or environment variable
    max_search_results = args.max_search_results
    if max_search_results == 5:  # If using default, check environment variable
        max_search_results = int(os.getenv('MAX_SEARCH_RESULTS', '5'))


    paths = {
        'song_identification': args.result_file if args.result_file else "song_identification_result.json",
    }
    result = identify_song_from_asr(transcript, paths, max_search_results=max_search_results)

    if result:
        song_title, artist_name, native_language, lyrics_content, lyrics_source_url = result
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