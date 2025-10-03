#!/usr/bin/env python3
"""
Script to translate LRC lyrics to Traditional Chinese using an OpenAI-compatible API.
"""

import os
import re
import argparse
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from logging_config import setup_logging, get_logger
from utils import load_prompt_template

logger = get_logger(__name__)

def read_lrc_file(file_path):
    """
    Read the LRC file and return its content as a string.
    
    Args:
        file_path (str): Path to the LRC file
        
    Returns:
        str: Content of the LRC file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def validate_lrc_content(content):
    """
    Validate that the LRC content has proper format.
    
    Args:
        content (str): LRC content to validate
        
    Returns:
        bool: True if content is valid LRC format, False otherwise
    """
    lines = content.strip().split('\n')
    
    # Check if we have at least one line
    if not lines or not lines[0].strip():
        logger.error("LRC content is empty")
        return False
    
    # Check for proper LRC timestamp format in at least some lines
    timestamp_pattern = r'\[([0-9]{2,3}:[0-9]{2}\.[0-9]{2,3}|[0-9]{2,3}:[0-9]{2})\]'
    has_timestamps = any(re.search(timestamp_pattern, line) for line in lines)
    
    if not has_timestamps:
        logger.warning("LRC content doesn't contain any timestamp patterns")
        return False
    
    # Additional validation could be added here
    logger.info("LRC content validation passed")
    return True


def get_prompt_file_for_language(target_language: str) -> str:
    """
    Get the appropriate prompt file name for the target language.

    Args:
        target_language (str): Target language for translation

    Returns:
        str: Prompt file name for the language
    """
    # Map language names to prompt file names
    language_prompt_map = {
        "Traditional Chinese": "lrc_traditional_chinese_prompt.txt",
        # Add more languages here as they are supported
        # "English": "lrc_english_prompt.txt",
        # "Japanese": "lrc_japanese_prompt.txt",
    }

    return language_prompt_map.get(target_language, "")


def translate_lrc_content(client, lrc_content, target_language="Traditional Chinese"):
    """
    Translate LRC content using an LLM, returning a bilingual LRC file.

    Args:
        client: OpenAI-compatible client instance
        lrc_content (str): Complete LRC file content to translate
        target_language (str): Target language for translation

    Returns:
        str: Translated bilingual LRC content, or None if not implemented
    """
    # Only support Traditional Chinese translation for now
    if target_language != "Traditional Chinese":
        logger.warning(f"Translation to '{target_language}' is not implemented. Only 'Traditional Chinese' is supported.")
        return None

    model = os.getenv("TRANSLATION_MODEL", os.getenv("OPENAI_MODEL", "qwen-plus"))

    # Get the appropriate prompt file for the target language
    prompt_file_name = get_prompt_file_for_language(target_language)
    if not prompt_file_name:
        logger.error(f"No prompt file configured for language: {target_language}")
        return None

    # Load prompt template from file
    prompt_template_path = os.path.join(os.path.dirname(__file__), "prompt", prompt_file_name)
    prompt_template = load_prompt_template(prompt_template_path)

    if not prompt_template:
        logger.error(f"Failed to load prompt template: {prompt_file_name}")
        return None

    # Format the prompt with actual data
    prompt = prompt_template.format(target_language=target_language, lrc_content=lrc_content)

    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for more consistent translation
            max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error translating LRC content: {e}")
        return None


def main(input_path, output_path, target_language="Traditional Chinese", log_level=logging.INFO):
    # Set up logging with specified level
    setup_logging(level=log_level)
    
    # Load configuration from environment variables
    base_url = os.getenv("OPENAI_BASE_URL", os.getenv("TRANSLATION_BASE_URL", "https://api-inference.modelscope.cn/v1"))
    api_key = os.getenv("OPENAI_API_KEY", os.getenv("TRANSLATION_API_KEY", ""))
    model = os.getenv("TRANSLATION_MODEL", os.getenv("OPENAI_MODEL", "qwen-plus"))
    
    logger.debug(f"Using base_url: {base_url}")
    logger.debug(f"Using model: {model}")
    
    if not api_key:
        logger.error("Error: API key not set in environment variables")
        return False
    
    # Initialize the OpenAI-compatible client with the custom base URL
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    
    # Check if the input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input LRC file does not exist: {input_path}")
        return False
    
    logger.info("Reading LRC file...")
    
    # Read the complete LRC file content
    lrc_content = read_lrc_file(input_path)
    logger.debug(f"Original LRC content length: {len(lrc_content)} characters")
    logger.debug(f"Original LRC content sample: {lrc_content[:300]}...")  # First 300 chars
    
    logger.info("Translating LRC content to bilingual format...")
    
    # Translate the entire LRC content
    translated_lrc_content = translate_lrc_content(client, lrc_content, target_language)
    
    if translated_lrc_content:
        logger.info("LRC content translated successfully!")
        logger.debug(f"Translated LRC content length: {len(translated_lrc_content)} characters")
        logger.debug(f"Translated LRC content sample: {translated_lrc_content[:300]}...")  # First 30 chars
        
        # Validate the translated content
        if validate_lrc_content(translated_lrc_content):
            logger.info("Translated LRC content validation passed")
        else:
            logger.warning("Translated LRC content validation failed, but saving anyway")
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save the translated LRC to a file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_lrc_content)
        
        logger.info(f"Bilingual LRC lyrics saved to: {output_path}")
        return True
    else:
        logger.error("Failed to translate LRC content.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate LRC lyrics to another language')
    parser.add_argument('input', nargs='?', help='Input LRC file path')
    parser.add_argument('-o', '--output', help='Output LRC file path')
    parser.add_argument('-l', '--language', default='Traditional Chinese', help='Target language for translation')
    
    args = parser.parse_args()
    
    # Use default paths if not provided
    input_path = args.input
    output_path = args.output or input_path.replace('.lrc', f'_{args.language.replace(" ", "_")}.lrc')
    
    success = main(input_path, output_path, args.language)
    if not success:
        exit(1)