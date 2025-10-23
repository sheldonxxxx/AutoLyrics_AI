#!/usr/bin/env python3
"""
Explain LRC lyrics in target language by analyzing the lyrics content without timestamps.

This module handles lyrics explanation for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/explain_lyrics.md

Key Features:
- Extract lyrics from LRC format (removing timestamps)
- Send lyrics to LLM for detailed explanation
- Support for multiple target languages
- Flexible API configuration
- Preserves original LRC structure for reference

Dependencies:
- pydantic-ai (structured LLM interactions)
- logging_config (pipeline logging)
- utils (file I/O and validation)

Supported Languages: Any language supported by the LLM (Traditional Chinese default)

Pipeline Stage: Enhancement (Optional post-processing step)
"""

import os
import logging

from logging_config import setup_logging, get_logger
from utils import (
    read_file,
    get_base_argparser,
    load_prompt_template,
    get_default_llm_config,
    get_prompt_file_for_language,
    remove_timestamps_from_transcript,
)
from agent_utils import prepare_agent

logger = get_logger(__name__)


def explain_lyrics_content(lrc_content, target_language="Traditional Chinese"):
    """
    Extract lyrics from LRC content and explain them using an LLM.

    Args:
        lrc_content (str): Complete LRC file content to analyze
        target_language (str): Target language for the explanation

    Returns:
        str: Explanation of the lyrics in target language, or None if explanation fails
    """

    # Extract only the lyrics content (without timestamps)
    lyrics_content = remove_timestamps_from_transcript(lrc_content)

    if not lyrics_content.strip():
        logger.warning("No lyrics content found in LRC file for explanation")
        return None

    # Get the appropriate prompt file for the target language
    prompt_file_name = get_prompt_file_for_language(target_language, "explanation")
    if not prompt_file_name:
        logger.exception(f"No prompt file configured for language: {target_language}")
        return None

    # Load prompt template from file
    system_prompt = load_prompt_template(
        prompt_file_name, target_language=target_language
    )

    if not system_prompt:
        logger.exception(f"Failed to load prompt template: {prompt_file_name}")
        return None

    try:
        # Get configuration for pydantic_ai
        config = get_default_llm_config()

        agent = prepare_agent(
            config["OPENAI_BASE_URL"],
            config["OPENAI_API_KEY"],
            config["OPENAI_MODEL"],
            instructions=system_prompt,
        )

        # Use the agent to perform explanation
        result = agent.run_sync(lyrics_content)

        if result and result.output:
            return result.output.strip()
        else:
            logger.exception("No result returned from explanation agent")
            return None

    except Exception as e:
        logger.exception(f"Error explaining LRC lyrics: {e}")
        return None


def main(
    input_path,
    output_path,
    target_language,
):
    # Get API configuration using utility function
    config = get_default_llm_config()

    logger.debug(f"Using base_url: {config['OPENAI_BASE_URL']}")
    logger.debug(f"Using model: {config['OPENAI_MODEL']}")

    # Check if the input file exists
    if not os.path.exists(input_path):
        logger.exception(f"Input LRC file does not exist: {input_path}")
        return False

    logger.info("Reading LRC file...")

    # Read the complete LRC file content
    lrc_content = read_file(input_path)
    logger.debug(f"Original LRC content length: {len(lrc_content)} characters")
    logger.debug(
        f"Original LRC content sample: {lrc_content[:300]}..."
    )  # First 300 chars

    logger.info("Extracting lyrics and sending to LLM for explanation...")

    # Explain the lyrics content
    explanation = explain_lyrics_content(lrc_content, target_language)

    if explanation:
        logger.info("Lyrics explained successfully!")
        logger.debug(f"Explanation length: {len(explanation)} characters")
        logger.debug(f"Explanation sample: {explanation[:300]}...")  # First 300 chars

        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Save the explanation to a file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(explanation)

        logger.info(f"Lyrics explanation saved to: {output_path}")
        return True
    else:
        logger.exception("Failed to explain lyrics.")
        return False


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    parser = get_base_argparser(description="Explain LRC lyrics in target language")

    parser.add_argument("input", nargs="?", help="Input LRC file path")
    parser.add_argument("-o", "--output", help="Output explanation file path")
    parser.add_argument(
        "-l",
        "--language",
        default="Traditional Chinese",
        help="Target language for explanation",
    )

    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Use default paths if not provided
    input_path = args.input
    if input_path:
        output_path = args.output or input_path.replace(
            ".lrc", f'_explanation_{args.language.replace(" ", "_")}.txt'
        )
    else:
        output_path = args.output

    success = main(
        input_path,
        output_path,
        args.language,
    )
    if not success:
        exit(1)
