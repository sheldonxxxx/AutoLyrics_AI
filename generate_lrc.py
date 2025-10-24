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

import logging
from pathlib import Path
from logging_config import setup_logging, get_logger
from utils import (
    read_file,
    get_base_argparser,
    load_prompt_template,
    convert_transcript_to_lrc,
    get_default_llm_config,
    validate_lrc_content,
)
from agent_utils import prepare_agent

logger = get_logger(__name__)


def generate_lrc_lyrics(asr_transcript: str,
                        lyrics_text: str,
                        paths: dict,
                        recompute: bool = False,
                        ) -> bool:
    """
    Generate LRC format lyrics by combining downloaded lyrics and ASR transcript
    using an LLM.

    Args:
        asr_transcript (str): ASR transcript with word-level timestamps
        lyrics_text (str): Downloaded lyrics text to align
        paths (dict): Dictionary containing file paths:
            - "lrc": Path to save the generated LRC file
        recompute (bool): If True, forces re-generation even if output exists

    Returns:
        bool: True if LRC generation succeeded, False otherwise
    """
    result_file_path = paths["lrc"]
    
    # Try to load existing result
    if not recompute and result_file_path.exists():
        logger.info(f"LRC lyrics already exist at: {result_file_path}")
        return True
    
    # Convert ASR transcript to LRC format for better alignment
    lrc_transcript = convert_transcript_to_lrc(asr_transcript)

    # Load prompt template from file
    system_prompt = load_prompt_template("lrc_generation_prompt.txt")

    if not system_prompt:
        logger.exception("Failed to load prompt template")
        return False

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
        
        if result and result.output and validate_lrc_content(result.output):
            logger.info("LRC lyrics generated successfully!")
            
            # Save the LRC lyrics to a file
            with open(result_file_path, "w", encoding="utf-8") as f:
                f.write(result.output.strip())
            logger.info(f"LRC lyrics saved to: {result_file_path}")
            return True
        else:
            logger.error("No result returned from LRC generation agent")
            return False
    except Exception:
        logger.exception("Error generating LRC lyrics")
        return False

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
    lyrics_file_path = Path(args.lyrics_file)
    transcript_file_path = Path(args.transcript_file)
    output_lrc_path = Path(args.output)

    # Check if the input files exist
    if not lyrics_file_path.exists():
        logger.exception(f"Lyrics file does not exist: {lyrics_file_path}")
        return

    if not transcript_file_path.exists():
        logger.exception(f"Transcript file does not exist: {transcript_file_path}")
        return

    logger.info("Reading lyrics and transcript files...")
    
    output_lrc_path.parent.mkdir(parents=True, exist_ok=True)
    
    paths = {
        "lyrics_txt": lyrics_file_path,
        "transcript_word_txt": transcript_file_path,
        "lrc": output_lrc_path,
    }

    logger.info("Generating LRC formatted lyrics...")
    
    asr_transcript = read_file(transcript_file_path)
    lyrics_text = read_file(lyrics_file_path)

    # Generate the LRC lyrics
    generate_lrc_lyrics(asr_transcript, lyrics_text, paths, recompute=args.recompute)


if __name__ == "__main__":
    main()
