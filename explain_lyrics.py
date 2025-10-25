#!/usr/bin/env python3
"""
Explain LRC lyrics in target language by analyzing the lyrics content without timestamps.

This module handles lyrics explanation for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/explain_lyrics.md

Key Features:
- Extract lyrics from LRC format (removing timestamps)
- Send lyrics to LLM for detailed explanation
- Support for multiple target languages
- Flexible API configuration
- Preserves original LRC structure for reference

Dependencies:
- pydantic-ai (structured LLM interactions)
- logging_config (pipeline logging)
- utils (file I/O and validation)

Supported Languages: Any language supported by the LLM (Traditional Chinese default)

Pipeline Stage: Enhancement (Optional post-processing step)
"""
import logging
from pathlib import Path

from utils import (
    setup_logging,
    get_logger,
    read_file,
    get_base_argparser,
    load_prompt_template,
    get_default_llm_config,
    get_prompt_file_for_language,
    remove_timestamps_from_transcript,
    prepare_agent,
)

logger = get_logger(__name__)


def explain_lyrics_content(lrc_content: str,
                           paths: dict,
                           target_language: str,
                           song_story: dict = None,
                           recompute: bool = False) -> bool:
    """
    Extract lyrics from LRC content and explain them using an LLM.

    Args:
        paths (dict): Dictionary containing file paths:
            - "explanation_txt": Path to save the explanation text file
        lrc_content (str): Complete LRC file content to analyze
        target_language (str): Target language for the explanation
        recompute (bool): If True, forces re-explanation even if output exists 
        
    Returns:
        str: Explanation of the lyrics in target language, or None if explanation fails
    """
    output_path = paths['explanation_txt']
    
    if not recompute and output_path.exists():
        logger.info(f"Lyrics explanation already exists at: {output_path}")
        return True

    # Extract only the lyrics content (without timestamps)
    lyrics_content = remove_timestamps_from_transcript(lrc_content)

    if not lyrics_content.strip():
        logger.warning("No lyrics content found in LRC file for explanation")
        return False

    # Get the appropriate prompt file for the target language
    prompt_file_name = get_prompt_file_for_language(target_language, "explanation")

    # Load prompt template from file
    system_prompt = load_prompt_template(
        prompt_file_name, target_language=target_language
    )

    if not system_prompt:
        logger.exception(f"Failed to load prompt template: {prompt_file_name}")
        return False
    
    user_prompt = f"Lyrics:\n{lyrics_content}\n\n"

    if song_story:
        user_prompt += f"Creation Story:\n{song_story['creation_story']}\n\n"
        user_prompt += f"Background Story:\n{song_story['background_story']}\n\n"

    try:
        # Get configuration for pydantic_ai
        config = get_default_llm_config()

        agent = prepare_agent(
            config["OPENAI_BASE_URL"],
            config["OPENAI_API_KEY"],
            config["OPENAI_MODEL"],
            instructions=system_prompt,
        )
        
        logger.info("Starting lyrics explanation...")

        # Use the agent to perform explanation
        result = agent.run_sync(user_prompt)

        if result and result.output:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.output.strip())
            logger.info(f"Lyrics explanation saved to: {output_path}")
            return True
        else:
            logger.error("No result returned from explanation agent")
            return False

    except Exception:
        logger.exception("Error explaining LRC lyrics")
        return False

def main():
    import dotenv
    dotenv.load_dotenv()

    parser = get_base_argparser(description="Explain LRC lyrics in target language")
    parser.add_argument("input", nargs="?", help="Input LRC file path")
    parser.add_argument("-o", "--output", help="Output explanation file path")
    parser.add_argument(
        "-l",
        "--language",
        default="Traditional Chinese",
        help="Target language for explanation",
    )
    args = parser.parse_args()

    # Set up logging with Logfire integration
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Use default paths if not provided
    input_path = Path(args.input)
    target_language = args.language
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(input_path.stem + f'_explanation_{args.language.replace(" ", "_")}.txt')

    # Check if the input file exists
    if not input_path.exists():
        logger.exception(f"Input LRC file does not exist: {input_path}")
        return False
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lrc_content = read_file(input_path)

    # Explain the lyrics content
    paths = {
        "explanation_txt": output_path,
    }
    explain_lyrics_content(lrc_content, paths, target_language, recompute=args.recompute)

if __name__ == "__main__":
    main()
