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

import logging
from pathlib import Path

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


def translate_lrc_content(
    lrc_content: str,
    paths: dict,
    target_language: str,
    song_explanation: str = None,
    recompute: bool = False,
) -> bool:
    """
    Translate LRC content using an LLM, returning a bilingual LRC file.

    Args:
        lrc_content (str): LRC content to translate
        paths (dict): Dictionary containing file paths:
            - "translated_lrc": Path to save the translated LRC file
        target_language (str): Target language for translation

    Returns:
        str: Translated bilingual LRC content, or None if translation fails
    """
    result_file_path = paths["translated_lrc"]

    # Try to load existing result
    if not recompute and result_file_path.exists():
        logger.info(f"Translated LRC lyrics already exist at: {result_file_path}")
        return True

    # Get the appropriate prompt file for the target language
    prompt_file_name = get_prompt_file_for_language(target_language, task="translation")

    # Load prompt template from file
    system_prompt = load_prompt_template(
        prompt_file_name, target_language=target_language
    )

    if not system_prompt:
        logger.error(f"Failed to load system prompt: {prompt_file_name}")
        return False
    
    user_prompt = ""
    
    if song_explanation:
        user_prompt += f"Song explanation:\n{song_explanation}\n\n"

    user_prompt += f"LRC content:\n{lrc_content}"

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
            if not validate_lrc_content(result.output):
                logger.error("Translated LRC content is not valid")
                return False
            logger.info("Successfully translated LRC content")
            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write(result.output.strip())
            logger.info(f"Translated LRC content saved to: {result_file_path}")
            return True
        else:
            logger.error("No result returned from translation agent")
            return False

    except Exception as e:
        logger.exception(f"Error translating LRC content: {e}")
        return False


def main():

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
    input_path = Path(args.input)
    output_path = (
        Path(args.output) if args.output else Path(f"{input_path.stem}_bilingual.lrc")
    )
    target_language = args.language

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if the input file exists
    if not input_path.exists():
        logger.error(f"Input LRC file does not exist: {input_path}")
        return False

    logger.info("Translating LRC content to bilingual format...")

    paths = {
        "translated_lrc": output_path,
    }

    lrc_content = read_file(input_path)

    # Translate the entire LRC content
    translate_lrc_content(
        lrc_content, paths, target_language, recompute=not args.recompute
    )


if __name__ == "__main__":
    main()
