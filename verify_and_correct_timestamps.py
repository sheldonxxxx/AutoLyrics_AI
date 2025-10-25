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

import logging
from pathlib import Path
from utils import (
    setup_logging,
    get_logger,
    load_prompt_template,
    get_default_llm_config,
    convert_transcript_to_lrc,
    get_base_argparser,
    read_file,
    validate_lrc_content,
    prepare_agent,
)

logger = get_logger(__name__)


def verify_and_correct_timestamps(
    lrc_content: str, asr_transcript: str, paths: dict, recompute: bool = False
) -> bool:
    """
    Verify and correct LRC timestamps using ASR transcript as reference.

    Compares LRC timestamps against ASR transcript timing and corrects any
    inaccuracies while preserving the original lyrics content exactly.

    Args:
        paths (dict): Dictionary containing file paths:
            - "lrc": Path to the LRC file to verify
            - "transcript_word_txt": Path to the ASR transcript file
            - "corrected_lrc": Path to save the corrected LRC file
        recompute (bool): If True, forces re-verification even if output exists

    Returns:
        bool: True if verification and correction succeeded, False otherwise
    """
    result_file_path = paths["corrected_lrc"]

    # Check if output already exists
    if not recompute and result_file_path.exists():
        logger.info(f"Corrected LRC already exists at: {result_file_path}")
        return True

    # Load prompt template from file
    asr_transcript = convert_transcript_to_lrc(asr_transcript)

    # Format the prompt with actual data
    system_prompt = load_prompt_template("lrc_timestamp_verification_prompt.txt")

    if not system_prompt:
        logger.exception("Failed to load timestamp verification prompt template")
        return False

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

        if result and result.output and validate_lrc_content(result.output):
            logger.info("Timestamp verification and correction completed successfully")

            # Count corrections by comparing original and corrected content
            corrected_lrc_content = result.output.strip()
            original_lines = set(lrc_content.strip().split("\n"))
            corrected_lines = set(corrected_lrc_content.split("\n"))
            corrections_count = len(
                original_lines.symmetric_difference(corrected_lines)
            )

            logger.info(f"Number of corrections applied: {corrections_count}")

            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write(result.output.strip())
            logger.info(f"Corrected LRC saved to: {result_file_path}")
            return True
        else:
            logger.error("No result returned from timestamp verification agent")
            return False

    except Exception:
        logger.exception("Error during timestamp verification and correction")
        return False


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
    lrc_file_path = Path(args.lrc_file)
    transcript_file_path = Path(args.transcript_file)
    output_lrc_path = Path(args.output)

    # Check if the input files exist
    if not lrc_file_path.exists():
        logger.exception(f"LRC file does not exist: {lrc_file_path}")
        return

    if not transcript_file_path.exists():
        logger.exception(f"Transcript file does not exist: {transcript_file_path}")
        return

    logger.info("Verifying and correcting LRC timestamps...")

    output_lrc_path.parent.mkdir(parents=True, exist_ok=True)

    paths = {
        "corrected_lrc": output_lrc_path,
    }

    asr_transcript = read_file(transcript_file_path)
    lrc_content = read_file(lrc_file_path)

    # Verify and correct timestamps
    verify_and_correct_timestamps(
        lrc_content, asr_transcript, paths, recompute=args.recompute
    )


if __name__ == "__main__":
    main()
