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
from dotenv import load_dotenv
import logging
from logging_config import setup_logging, get_logger
from utils import load_prompt_template, get_default_llm_config, convert_transcript_to_lrc
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

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
    prompt = load_prompt_template("lrc_timestamp_verification_prompt.txt", lrc_content=lrc_content, asr_transcript=asr_transcript)

    if not prompt:
        logger.exception("Failed to load timestamp verification prompt template")
        return None

    try:
        # Get configuration for pydantic_ai
        config = get_default_llm_config()

        # Create OpenAI provider with custom configuration
        openai_provider = OpenAIProvider(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"]
        )

        # Create OpenAI model with the provider
        openai_model = OpenAIChatModel(
            config["OPENAI_MODEL"],
            provider=openai_provider
        )

        # Create Pydantic AI agent for timestamp verification and correction
        agent = Agent(
            openai_model,
            retries=3
        )

        # Use the agent to verify and correct timestamps
        result = agent.run_sync(prompt)

        if result and result.output:
            corrected_lrc = result.output.strip()
            logger.info("Timestamp verification and correction completed successfully")
            logger.debug(f"Corrected LRC content length: {len(corrected_lrc)} characters")
            return corrected_lrc
        else:
            logger.exception("No result returned from timestamp verification agent")
            return None

    except Exception as e:
        logger.exception(f"Error during timestamp verification and correction: {e}")
        return None

def main():
    """Main function for command-line usage of timestamp verification."""
    import argparse
    parser = argparse.ArgumentParser(description='Verify and correct LRC file timestamps using ASR transcript as reference via Pydantic AI.')
    parser.add_argument('--lrc-file', '-l',
                        help='Path to the LRC file to verify and correct')
    parser.add_argument('--transcript-file', '-t',
                        help='Path to the ASR transcript file')
    parser.add_argument('--output', '-o',
                        help='Output corrected LRC file path')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--logfire', action='store_true',
                        help='Enable Logfire integration')

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
        with open(lrc_file_path, 'r', encoding='utf-8') as f:
            lrc_content = f.read()

        with open(transcript_file_path, 'r', encoding='utf-8') as f:
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
            with open(output_lrc_path, 'w', encoding='utf-8') as f:
                f.write(corrected_lrc)

            logger.info(f"Corrected LRC file saved to: {output_lrc_path}")
        except Exception as e:
            logger.exception(f"Error saving corrected LRC file: {e}")
    else:
        logger.exception("Failed to verify and correct LRC timestamps.")


if __name__ == "__main__":
    main()