#!/usr/bin/env python3
"""
Script to identify song name and artist from ASR transcript using LLM and web search.
"""

import os
import logging
import json
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from pathlib import Path
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
from logging_config import get_logger
from utils import get_openai_config, load_prompt_template

logger = get_logger(__name__)


class SearXNGSearchTool(BaseTool):
    """Custom tool for searching with SearXNG."""

    name: str = "searxng_search"
    description: str = "Search the web using SearXNG metasearch engine"
    searxng_url: str = Field(default_factory=lambda: os.getenv("SEARXNG_URL") or "")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Validate SearXNG URL configuration
        if not self.searxng_url:
            print("ERROR: SEARXNG_URL not found in environment variables.")
            print("Please add SEARXNG_URL to your .env file, for example:")
            print("SEARXNG_URL=http://localhost:8888")
            print("Or set the environment variable directly.")
            exit(1)

    def _run(self, query: str) -> str:
        """Execute the SearXNG search."""
        try:
            # SearXNG API parameters
            params = {
                'q': query,
                'format': 'json',
                # 'language': 'ja',
                'categories': 'general,music',
                'engines': 'google,bing,duckduckgo'
            }

            logger.info(f"Searching SearXNG at {self.searxng_url} with query: {query}")

            # Make request to SearXNG
            response = requests.get(
                f"{self.searxng_url}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Format results for LLM
            if 'results' in data:
                results = []
                for result in data['results'][:5]:  # Limit to top 5 results
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
                    })

                # Create a formatted string for the LLM
                formatted_results = f"Search results for '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    formatted_results += f"{i}. **{result['title']}**\n"
                    formatted_results += f"   URL: {result['url']}\n"
                    formatted_results += f"   Content: {result['content']}\n\n"

                return formatted_results
            else:
                return f"No search results found for '{query}'"

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

        # Initialize the LLM with tool binding
        self.llm = ChatOpenAI(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"],
            model=config["OPENAI_MODEL"],
            temperature=0.1
        )

        # Initialize SearXNG search tool
        self.search_tool = SearXNGSearchTool()

        # Initialize the LLM for tool interactions (without structured output)
        self.llm_with_tools = self.llm.bind_tools([self.search_tool])

    def identify_song(self, transcript: str) -> Optional[SongIdentification]:
        """
        Identify song name and artist from ASR transcript.

        Args:
            transcript (str): ASR transcript of the song vocals

        Returns:
            Optional[SongIdentification]: Identified song information or None if identification fails
        """
        try:
            # Load prompt template from file
            prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", "song_identification_prompt.txt")
            prompt_template = load_prompt_template(prompt_template_path)

            if not prompt_template:
                logger.error("Failed to load song identification prompt template")
                return None

            # Generate JSON schema from SongIdentification model
            json_schema = SongIdentification.model_json_schema()

            # Format the prompt with actual data and JSON schema (escape for template)
            prompt = prompt_template.format(
                transcript=transcript[:2000],
                json_schema=json.dumps(json_schema, indent=2)
            )

            # Start conversation with the prompt
            messages = [HumanMessage(content=prompt)]

            # Run the LLM with tools until no more tool calls
            max_iterations = 10  # Safety limit to prevent infinite loops
            for iteration in range(max_iterations):
                logger.info(f"LLM tool iteration {iteration + 1}")

                # Get response from LLM
                response = self.llm_with_tools.invoke(messages)

                # Check if LLM wants to use tools
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Add the LLM's response to messages
                    messages.append(response)

                    # Execute the tool calls
                    for tool_call in response.tool_calls:
                        logger.info(f"Executing tool call: {tool_call}")

                        # Execute the SearXNG search tool
                        if tool_call['name'] == 'searxng_search':
                            # Extract the query from tool args
                            query = tool_call['args'].get('query', '')
                            tool_result = self.search_tool._run(query)
                        else:
                            tool_result = f"Unknown tool: {tool_call['name']}"

                        # Add tool result to messages
                        messages.append(ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call['id']
                        ))

                    logger.info(f"Tool calls executed, continuing conversation...")
                else:
                    # LLM has finished and provided a final answer
                    logger.info("LLM finished using tools, processing final response")
                    break

            if iteration == max_iterations - 1:
                logger.warning(f"Reached maximum iterations ({max_iterations}), stopping tool use")

            # Get the final response content for structured parsing
            final_content = response.content if hasattr(response, 'content') else str(response)

            try:
                # Parse JSON response manually (no structured output due to API compatibility)
                if "```json" in final_content:
                    json_str = final_content.split("```json")[1].split("```")[0].strip()
                elif "{" in final_content:
                    # Find JSON object in text
                    start = final_content.find("{")
                    end = final_content.rfind("}") + 1
                    json_str = final_content[start:end]
                else:
                    json_str = final_content

                result_data = json.loads(json_str)

                # Create SongIdentification object
                result = SongIdentification(
                    song_title=result_data.get('song_title', ''),
                    artist_name=result_data.get('artist_name', ''),
                    confidence_score=float(result_data.get('confidence_score', 0.0)),
                    native_language=result_data.get('native_language', result_data.get('language', '')),
                    search_queries_used=result_data.get('search_queries_used', []),
                    reasoning=result_data.get('reasoning', '')
                )

                # Validate the result
                if result and result.confidence_score > 0.3:
                    logger.info(f"Successfully identified song: {result.song_title} by {result.artist_name} (confidence: {result.confidence_score})")
                    return result
                else:
                    logger.warning(f"Low confidence identification: {result.confidence_score if result else 'None'}")
                    return None

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {final_content}")
                return None

        except Exception as e:
            logger.error(f"Error during song identification: {e}")
            return None


def identify_song_from_asr(transcript: str, result_file_path: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
    """
    Convenience function to identify song from ASR transcript with optional caching.

    Args:
        transcript (str): ASR transcript of the song vocals
        result_file_path (Optional[str]): Path to save/load identification results

    Returns:
        Optional[Tuple[str, str, str]]: (song_title, artist_name, native_language) if identified, None otherwise
    """
    # Try to load existing result if file path provided
    if result_file_path and Path(result_file_path).exists():
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
    try:
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

    except Exception as e:
        logger.error(f"Failed to initialize song identifier: {e}")
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