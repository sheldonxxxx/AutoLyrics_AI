#!/usr/bin/env python3
"""
Generate synchronized LRC files by combining lyrics with ASR transcript timestamps.

This module is the core of the Music Lyrics Processing Pipeline, responsible for
creating synchronized LRC (Lyrics) files using AI-powered alignment.
For comprehensive documentation, see: docs/modules/generate_lrc.md

Key Features:
- Intelligent lyrics-to-timing alignment using LLM
- Dual input support (with/without reference lyrics)
- Grammar correction for ASR transcripts
- Proper LRC format compliance ([mm:ss.xx] timestamps)

LRC Format: [mm:ss.xx]Lyrics content with precise timing

Pipeline Stage: 5/6 (LRC Generation)
"""

import os
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger
from utils import (
    read_file,
    get_base_argparser,
    load_prompt_template,
    convert_transcript_to_lrc,
    get_default_llm_config,
)
from agent_utils import prepare_agent

logger = get_logger(__name__)


def generate_lrc_lyrics(lyrics_text: str, 
                        asr_transcript: str,
                        paths: dict,
                        force_recompute: bool = False,
                        ) -> str | None:
    """
    Generate LRC format lyrics by combining downloaded lyrics and ASR transcript
    using an LLM.

    Args:
        lyrics_text (str): Downloaded lyrics text
        asr_transcript (str): ASR transcript with timestamps
        model (str): Model name to use for generation

    Returns:
        str: LRC formatted lyrics
    """
    result_file_path = str(paths["lrc"])
    
    # Try to load existing result
    if not force_recompute and os.path.exists(result_file_path):
        try:
            cached_result = read_file(result_file_path)
            if cached_result.strip():
                logger.info(f"Loaded cached LRC lyrics from: {result_file_path}")
                return cached_result.strip()
        except Exception as e:
            logger.warning(f"Failed to read cached LRC lyrics: {e}")
    
    # Convert ASR transcript to LRC format for better alignment
    lrc_transcript = convert_transcript_to_lrc(asr_transcript)

    # Load prompt template from file
    system_prompt = load_prompt_template("lrc_generation_prompt.txt")

    if not system_prompt:
        logger.exception("Failed to load prompt template")
        return None

    user_prompt = f"Reference Lyrics:\n{lyrics_text}\n\nASR Transcript with word level timestamps:\n{lrc_transcript}"

    try:
        # Get configuration for pydantic_ai
        config = get_default_llm_config()

        agent = prepare_agent(
            config["OPENAI_BASE_URL"],
            config["OPENAI_API_KEY"],
            config["OPENAI_MODEL"],
            instructions=system_prompt,
        )

        # Use the agent to generate LRC
        result = agent.run_sync(user_prompt)
    except Exception as e:
        logger.exception(f"Error generating LRC lyrics: {e}")
        return None
    
    logger.info("LRC lyrics generated successfully!")
    
    if result and result.output:
        try:
            # Create directory if it doesn't exist
            Path(result_file_path).parent.mkdir(parents=True, exist_ok=True)

            # Save the LRC lyrics to a file
            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write(result.output.strip())

            logger.info(f"LRC lyrics saved to: {result_file_path}")
        except Exception as e:
            logger.exception("Failed to save LRC lyrics to file")
            return 
    else:
        logger.exception("No result returned from LRC generation agent")
        return


def main():
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    # Set up argument parser
    parser = get_base_argparser(
        description="Generate LRC format lyrics by combining downloaded lyrics and ASR output using AI"
    )

    parser.add_argument("--lyrics-file", "-l", help="Path to the lyrics file")
    parser.add_argument("--transcript-file", "-t", help="Path to the transcript file")
    parser.add_argument("--output", "-o", help="Output LRC file path")

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Define file paths
    lyrics_file_path = args.lyrics_file
    transcript_file_path = args.transcript_file
    output_lrc_path = args.output

    # Check if the input files exist
    if not os.path.exists(lyrics_file_path):
        logger.exception(f"Lyrics file does not exist: {lyrics_file_path}")
        return

    if not os.path.exists(transcript_file_path):
        logger.exception(f"Transcript file does not exist: {transcript_file_path}")
        return

    logger.info("Reading lyrics and transcript files...")

    # Read the lyrics and transcript
    lyrics_text = read_file(lyrics_file_path)
    asr_transcript = read_file(transcript_file_path)
    
    paths = {
        "lrc": output_lrc_path,
    }

    logger.info("Generating LRC formatted lyrics...")

    # Generate the LRC lyrics
    generate_lrc_lyrics(lyrics_text, asr_transcript, paths)


if __name__ == "__main__":
    main()
