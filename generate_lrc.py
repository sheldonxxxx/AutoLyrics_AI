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
from dotenv import load_dotenv
import logging
from logging_config import setup_logging, get_logger
from utils import load_prompt_template, read_file, convert_transcript_to_lrc, get_default_llm_config
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

def generate_lrc_lyrics(lyrics_text, asr_transcript):
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
    # Convert ASR transcript to LRC format for better alignment
    lrc_transcript = convert_transcript_to_lrc(asr_transcript)

    # Load prompt template from file
    prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", "lrc_generation_prompt.txt")
    prompt_template = load_prompt_template(prompt_template_path)

    if not prompt_template:
        logger.exception("Failed to load prompt template")
        return None

    # Format the prompt with actual data
    prompt = prompt_template.format(lyrics_text=lyrics_text, lrc_transcript=lrc_transcript)

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

        # Create Pydantic AI agent for LRC generation
        agent = Agent(
            openai_model,
            retries=3
        )

        # Use the agent to generate LRC
        result = agent.run_sync(prompt)

        if result and result.output:
            return result.output.strip()
        else:
            logger.exception("No result returned from LRC generation agent")
            return None

    except Exception as e:
        logger.exception(f"Error generating LRC lyrics: {e}")
        return None


def correct_grammar_in_transcript(asr_transcript, filename=None):
    """
    Correct grammatical errors in ASR transcript using an LLM.

    Args:
        asr_transcript (str): Raw ASR transcript that may contain grammatical errors
        filename (str, optional): Original audio filename for context
        model (str): Model name to use for correction

    Returns:
        str: Grammatically corrected transcript
    """
    
    lrc_transcript = convert_transcript_to_lrc(asr_transcript)

    # Load prompt template from file
    prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", "grammatical_correction_prompt.txt")
    prompt_template = load_prompt_template(prompt_template_path)

    if not prompt_template:
        logger.exception("Failed to load grammatical correction prompt template")
        return lrc_transcript  # Return original if prompt loading fails

    # Format the prompt with actual data
    prompt = prompt_template.format(asr_transcript=lrc_transcript, filename=filename or "Unknown")

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

        # Create Pydantic AI agent for grammar correction
        agent = Agent(
            openai_model,
            retries=3
        )

        # Use the agent to correct grammar
        result = agent.run_sync(prompt)

        if result and result.output:
            corrected_transcript = result.output.strip()
            logger.info("Grammatical correction completed successfully")
            return corrected_transcript
        else:
            logger.exception("No result returned from grammar correction agent")
            return asr_transcript

    except Exception as e:
        logger.exception(f"Error correcting grammar in transcript: {e}")
        return asr_transcript  # Return original if correction fails

def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Generate LRC format lyrics by combining downloaded lyrics and ASR output using an OpenAI-compatible API via Pydantic AI.')
    parser.add_argument('--lyrics-file', '-l',
                        help='Path to the lyrics file')
    parser.add_argument('--transcript-file', '-t',
                        help='Path to the transcript file')
    parser.add_argument('--output', '-o',
                        help='Output LRC file path')
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
    
    logger.info("Generating LRC formatted lyrics...")
    
    # Generate the LRC lyrics
    lrc_lyrics = generate_lrc_lyrics(lyrics_text, asr_transcript)
    
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
        logger.exception("Failed to generate LRC lyrics.")


if __name__ == "__main__":
    main()