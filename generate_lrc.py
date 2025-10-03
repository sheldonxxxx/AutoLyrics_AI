#!/usr/bin/env python3
"""
Script to generate LRC format lyrics by combining downloaded lyrics and ASR output
using an OpenAI-compatible API with a custom base URL.
"""

import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import logging
from logging_config import setup_logging, get_logger
from utils import load_prompt_template

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()


def read_lyrics_file(file_path):
    """
    Read the downloaded lyrics from file.
    
    Args:
        file_path (str): Path to the lyrics file
        
    Returns:
        str: Content of the lyrics file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_transcript_file(file_path):
    """
    Read the ASR transcript from file.
    
    Args:
        file_path (str): Path to the transcript file
        
    Returns:
        str: Content of the transcript file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def convert_transcript_to_lrc(transcript_text):
    """
    Convert the ASR transcript to LRC format for better alignment.
    
    Args:
        transcript_text (str): ASR transcript with timestamps
        
    Returns:
        str: Transcript in LRC format
    """
    lines = transcript_text.split('\n')
    lrc_lines = []
    
    for line in lines:
        # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
        match = re.match(r'\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)', line.strip())
        if match:
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            text = match.group(3).strip()
            
            if text:  # Only add non-empty lines
                # Convert seconds to [mm:ss.xx] format
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                hundredths = int((start_time % 1) * 100)
                lrc_line = f'[{minutes:02d}:{seconds:02d}.{hundredths:02d}]{text}'
                lrc_lines.append(lrc_line)
    
    return '\n'.join(lrc_lines)


def generate_lrc_lyrics(client, lyrics_text, asr_transcript):
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

    model = os.getenv("OPENAI_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")
    # model = "deepseek-ai/DeepSeek-R1-0528"

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
            temperature=0.1,  # Low temperature for more consistent output
            # max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating LRC lyrics: {e}")
        return None

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
    
    # Load configuration from environment variables
    base_url = os.getenv("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key:
        logger.error("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize the OpenAI client with the custom base URL
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
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
    lrc_lyrics = generate_lrc_lyrics(client, lyrics_text, asr_transcript)
    
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