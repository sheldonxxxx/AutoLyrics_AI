#!/usr/bin/env python3
"""
Verify and correct LRC file timestamps using ASR transcript as reference.

This module verifies timestamp accuracy in LRC files by comparing them against
the original ASR transcript and corrects any timing issues while preserving
the original lyrics content exactly as provided.

For comprehensive documentation, see: docs/modules/verify_and_correct_timestamps.md

Key Features:
- Timestamp verification against ASR transcript ground truth
- Precision timestamp correction without lyrics modification
- Pydantic AI integration for intelligent timing alignment
- LRC format compliance and validation

Pipeline Stage: 5.5/6 (Timestamp Verification and Correction)
"""

import os
import logging
from logging_config import setup_logging, get_logger
from utils import (
    load_prompt_template,
    get_default_llm_config,
    convert_transcript_to_lrc,
    get_base_argparser,
)
from agent_utils import prepare_agent

logger = get_logger(__name__)


def verify_and_correct_timestamps(lrc_content: str, asr_transcript: str) -> str | None:
    """
    Verify and correct LRC timestamps using ASR transcript as reference.

    Compares LRC timestamps against ASR transcript timing and corrects any
    inaccuracies while preserving the original lyrics content exactly.

    Args:
        lrc_content (str): Current LRC content with potentially incorrect timestamps
        asr_transcript (str): ASR transcript with accurate word-level timestamps

    Returns:
        str | None: Corrected LRC content with fixed timestamps, or None if error
    """
    # Load prompt template from file
    asr_transcript = convert_transcript_to_lrc(asr_transcript)

    # Format the prompt with actual data
    system_prompt = load_prompt_template("lrc_timestamp_verification_prompt.txt")

    if not system_prompt:
        logger.exception("Failed to load timestamp verification prompt template")
        return None

    user_prompt = f"ASR Transcript:\n{asr_transcript}\n\nLRC Content:\n{lrc_content}"
    try:
        # Get configuration for pydantic_ai
        config = get_default_llm_config()

        agent = prepare_agent(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"],
            model=config["OPENAI_MODEL"],
            instructions=system_prompt,
        )

        # Use the agent to verify and correct timestamps
        result = agent.run_sync(user_prompt)

        if result and result.output:
            corrected_lrc = result.output.strip()
            logger.info("Timestamp verification and correction completed successfully")
            logger.debug(
                f"Corrected LRC content length: {len(corrected_lrc)} characters"
            )
            return corrected_lrc
        else:
            logger.exception("No result returned from timestamp verification agent")
            return None

    except Exception as e:
        logger.exception(f"Error during timestamp verification and correction: {e}")
        return None


def main():
    """Main function for command-line usage of timestamp verification."""
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    parser = get_base_argparser(
        description="Verify and correct LRC file timestamps using ASR transcript as reference"
    )

    parser.add_argument(
        "--lrc-file", "-l", help="Path to the LRC file to verify and correct"
    )
    parser.add_argument(
        "--transcript-file", "-t", help="Path to the ASR transcript file"
    )
    parser.add_argument("--output", "-o", help="Output corrected LRC file path")

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Define file paths
    lrc_file_path = args.lrc_file
    transcript_file_path = args.transcript_file
    output_lrc_path = args.output

    # Check if the input files exist
    if not os.path.exists(lrc_file_path):
        logger.exception(f"LRC file does not exist: {lrc_file_path}")
        return

    if not os.path.exists(transcript_file_path):
        logger.exception(f"Transcript file does not exist: {transcript_file_path}")
        return

    logger.info("Reading LRC and transcript files...")

    # Read the LRC and transcript content
    try:
        with open(lrc_file_path, "r", encoding="utf-8") as f:
            lrc_content = f.read()

        with open(transcript_file_path, "r", encoding="utf-8") as f:
            asr_transcript = f.read()

    except Exception as e:
        logger.exception(f"Error reading input files: {e}")
        return

    logger.info("Verifying and correcting LRC timestamps...")

    # Verify and correct timestamps
    corrected_lrc = verify_and_correct_timestamps(lrc_content, asr_transcript)

    if corrected_lrc:
        logger.info("LRC timestamps verified and corrected successfully!")

        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_lrc_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Save the corrected LRC content to a file
        try:
            with open(output_lrc_path, "w", encoding="utf-8") as f:
                f.write(corrected_lrc)

            logger.info(f"Corrected LRC file saved to: {output_lrc_path}")
        except Exception as e:
            logger.exception(f"Error saving corrected LRC file: {e}")
    else:
        logger.exception("Failed to verify and correct LRC timestamps.")


if __name__ == "__main__":
    main()
