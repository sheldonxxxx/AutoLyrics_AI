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

Dependencies:
- openai (API client library)
- logging_config (pipeline logging)
- utils (file I/O and validation)

LRC Format: [mm:ss.xx]Lyrics content with precise timing

Pipeline Stage: 5/6 (LRC Generation)
"""

import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import logging
from logging_config import setup_logging, get_logger
from utils import load_prompt_template, read_lyrics_file, read_transcript_file, convert_transcript_to_lrc, get_openai_config

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()


def generate_lrc_lyrics(client, lyrics_text, asr_transcript, model=None):
    """
    Generate LRC format lyrics by combining downloaded lyrics and ASR transcript
    using an LLM.

    Args:
        client: OpenAI client instance
        lyrics_text (str): Downloaded lyrics text
        asr_transcript (str): ASR transcript with timestamps

    Returns:
        str: LRC formatted lyrics
    """
    # Convert ASR transcript to LRC format for better alignment
    lrc_transcript = convert_transcript_to_lrc(asr_transcript)

    if model is None:
        logger.error("Model parameter is required")
        return None

    # Load prompt template from file
    prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", "lrc_generation_prompt.txt")
    prompt_template = load_prompt_template(prompt_template_path)

    if not prompt_template:
        logger.error("Failed to load prompt template")
        return None

    # Format the prompt with actual data
    prompt = prompt_template.format(lyrics_text=lyrics_text, lrc_transcript=lrc_transcript)
    
    try:
        response = client.chat.completions.create(
            model=model,  # Use model from environment variable
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            extra_body={"enable_thinking": False},
            temperature=0.1,  # Low temperature for more consistent output
            # max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Error generating LRC lyrics: {e}")
        return None


def correct_grammar_in_transcript(client, asr_transcript, filename=None, model=None):
    """
    Correct grammatical errors in ASR transcript using an LLM.

    Args:
        client: OpenAI client instance
        asr_transcript (str): Raw ASR transcript that may contain grammatical errors
        filename (str, optional): Original audio filename for context

    Returns:
        str: Grammatically corrected transcript
    """
    if model is None:
        logger.error("Model parameter is required")
        return asr_transcript  # Return original if model not provided

    # Load prompt template from file
    prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", "grammatical_correction_prompt.txt")
    prompt_template = load_prompt_template(prompt_template_path)

    if not prompt_template:
        logger.error("Failed to load grammatical correction prompt template")
        return asr_transcript  # Return original if prompt loading fails

    # Format the prompt with actual data
    prompt = prompt_template.format(asr_transcript=asr_transcript, filename=filename or "Unknown")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent corrections
        )

        corrected_transcript = response.choices[0].message.content.strip()
        logger.info("Grammatical correction completed successfully")
        return corrected_transcript

    except Exception as e:
        logger.error(f"Error correcting grammar in transcript: {e}")
        return asr_transcript  # Return original if correction fails

def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Generate LRC format lyrics by combining downloaded lyrics and ASR output using an OpenAI-compatible API.')
    parser.add_argument('--lyrics-file', '-l',
                        help='Path to the lyrics file')
    parser.add_argument('--transcript-file', '-t',
                        help='Path to the transcript file')
    parser.add_argument('--output', '-o',
                        help='Output LRC file path')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)
    
    # Get OpenAI configuration using utility function
    config = get_openai_config()

    # Initialize the OpenAI client with the custom base URL
    client = OpenAI(
        base_url=config["OPENAI_BASE_URL"],
        api_key=config["OPENAI_API_KEY"]
    )
    
    # Define file paths
    lyrics_file_path = args.lyrics_file
    transcript_file_path = args.transcript_file
    output_lrc_path = args.output
    
    # Check if the input files exist
    if not os.path.exists(lyrics_file_path):
        logger.error(f"Lyrics file does not exist: {lyrics_file_path}")
        return
    
    if not os.path.exists(transcript_file_path):
        logger.error(f"Transcript file does not exist: {transcript_file_path}")
        return
    
    logger.info("Reading lyrics and transcript files...")
    
    # Read the lyrics and transcript
    lyrics_text = read_lyrics_file(lyrics_file_path)
    asr_transcript = read_transcript_file(transcript_file_path)
    
    logger.info("Generating LRC formatted lyrics...")
    
    # Generate the LRC lyrics
    lrc_lyrics = generate_lrc_lyrics(client, lyrics_text, asr_transcript, config["OPENAI_MODEL"])
    
    if lrc_lyrics:
        logger.info("LRC lyrics generated successfully!")
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_lrc_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save the LRC lyrics to a file
        with open(output_lrc_path, 'w', encoding='utf-8') as f:
            f.write(lrc_lyrics)
        
        logger.info(f"LRC lyrics saved to: {output_lrc_path}")
    else:
        logger.error("Failed to generate LRC lyrics.")


if __name__ == "__main__":
    main()