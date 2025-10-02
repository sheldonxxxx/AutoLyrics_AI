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


def translate_lrc_content(client, lrc_content, target_language="Traditional Chinese"):
    """
    Translate LRC content using an LLM, returning a bilingual LRC file.
    
    Args:
        client: OpenAI-compatible client instance
        lrc_content (str): Complete LRC file content to translate
        target_language (str): Target language for translation
        
    Returns:
        str: Translated bilingual LRC content
    """
    model = os.getenv("TRANSLATION_MODEL", os.getenv("OPENAI_MODEL", "qwen-plus"))
    
    # Chinese prompt using prompt engineering techniques
    prompt = f"""
你是一位专业的歌词翻译专家，精通中日/中英歌词翻译。你的任务是将包含时间戳的歌词（LRC格式）翻译成{target_language}，并生成一个双语LRC文件。

角色设定：
- 你是歌词翻译专家，精通{target_language}，了解歌词的韵律和意境
- 你熟悉LRC格式（[mm:ss.xx]歌词内容 或 [mm:ss]歌词内容）

输入格式：
- 输入是一个LRC格式的歌词文件，包含时间戳和原歌词
- 格式为：[mm:ss.xx]歌词内容 或 [mm:ss]歌词内容
- 可能包含元数据行，如[ti:], [ar:], [al:], [by:], [offset:]等

输出要求：
1. 保持原有LRC格式不变
2. 为每行有歌词的时间戳行添加对应的{target_language}翻译
3. 翻译应紧跟在原歌词行之后，使用相同的时间戳
4. 保持所有元数据行（如[ti:], [ar:], [al:], [by:], [offset:]等）不变
5. 确保翻译准确传达原歌词的含义和情感
6. 如果某行没有歌词内容（只有时间戳），则不添加翻译

示例输入：
[ti:歌曲标题]
[ar:歌手]
[00:12.34]春が来た
[00:15.67]花が咲いてる
[00:18.90]風が優しく吹いてる

示例输出：
[ti:歌曲标题]
[ar:歌手]
[00:12.34]春が来た
[00:12.34]春天来了
[00:15.67]花が咲いてる
[00:15.67]花儿正盛开
[00:18.90]風が優しく吹いてる
[00:18.90]微风轻柔地吹着

现在请翻译以下LRC歌词内容，生成一个完整的双语LRC文件：
{lrc_content}

{target_language}双语LRC歌词：
"""

    
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