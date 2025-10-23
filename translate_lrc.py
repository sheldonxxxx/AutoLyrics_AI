#!/usr/bin/env python3
"""
Translate LRC lyrics to Traditional Chinese creating bilingual synchronized lyrics.

This module handles LRC translation for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/translate_lrc.md

Key Features:
- Bilingual LRC format with preserved timing
- Cultural adaptation and context preservation
- Flexible API configuration (translation-specific or fallback)
- LRC format compliance and validation

Dependencies:
- pydantic-ai (structured LLM interactions)
- logging_config (pipeline logging)
- utils (file I/O and validation)

Supported Languages: Traditional Chinese (extensible architecture)

Pipeline Stage: 6/6 (Translation)
"""

import os
import logging

from logging_config import setup_logging, get_logger
from utils import (
    read_file,
    get_base_argparser,
    load_prompt_template,
    validate_lrc_content,
    get_prompt_file_for_language,
    get_translation_config,
)
from agent_utils import prepare_agent

logger = get_logger(__name__)


def translate_lrc_content(lrc_content, target_language="Traditional Chinese"):
    """
    Translate LRC content using an LLM, returning a bilingual LRC file.

    Args:
        lrc_content (str): Complete LRC file content to translate
        target_language (str): Target language for translation
        model (str): Model name to use for translation

    Returns:
        str: Translated bilingual LRC content, or None if translation fails
    """

    # Get the appropriate prompt file for the target language
    prompt_file_name = get_prompt_file_for_language(target_language, task="translation")
    if not prompt_file_name:
        logger.exception(f"No prompt file configured for language: {target_language}")
        return None

    # Load prompt template from file
    system_prompt = load_prompt_template(
        prompt_file_name, target_language=target_language
    )

    if not system_prompt:
        logger.exception(f"Failed to load system prompt: {prompt_file_name}")
        return None

    user_prompt = lrc_content

    try:
        # Get configuration for pydantic_ai
        config = get_translation_config()

        agent = prepare_agent(
            config["base_url"],
            config["api_key"],
            config["model"],
            instructions=system_prompt,
        )

        # Use the agent to perform translation
        result = agent.run_sync(user_prompt)

        if result and result.output:
            return result.output.strip()
        else:
            logger.exception("No result returned from translation agent")
            return None

    except Exception as e:
        logger.exception(f"Error translating LRC content: {e}")
        return None


def main(input_path, output_path, target_language):

    # Get translation configuration using utility function
    config = get_translation_config()

    logger.debug(f"Using base_url: {config['base_url']}")
    logger.debug(f"Using model: {config['model']}")

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

    logger.info("Translating LRC content to bilingual format...")

    # Translate the entire LRC content
    translated_lrc_content = translate_lrc_content(lrc_content, target_language)

    if translated_lrc_content:
        logger.info("LRC content translated successfully!")
        logger.debug(
            f"Translated LRC content length: {len(translated_lrc_content)} characters"
        )
        logger.debug(
            f"Translated LRC content sample: {translated_lrc_content[:300]}..."
        )  # First 30 chars

        # Validate the translated content
        if validate_lrc_content(translated_lrc_content):
            logger.info("Translated LRC content validation passed")
        else:
            logger.warning(
                "Translated LRC content validation failed, but saving anyway"
            )

        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Save the translated LRC to a file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(translated_lrc_content)

        logger.info(f"Bilingual LRC lyrics saved to: {output_path}")
        return True
    else:
        logger.exception("Failed to translate LRC content.")
        return False


if __name__ == "__main__":
    parser = get_base_argparser(description="Translate LRC lyrics to another language")
    parser.add_argument("input", nargs="?", help="Input LRC file path")
    parser.add_argument("-o", "--output", help="Output LRC file path")
    parser.add_argument(
        "-l",
        "--language",
        default="Traditional Chinese",
        help="Target language for translation",
    )

    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Use default paths if not provided
    input_path = args.input
    output_path = args.output or input_path.replace(
        ".lrc", f'_{args.language.replace(" ", "_")}.lrc'
    )

    success = main(input_path, output_path, args.language, logfire_enabled=args.logfire)
    if not success:
        exit(1)
