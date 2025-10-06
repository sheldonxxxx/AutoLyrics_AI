#!/usr/bin/env python3
"""
Shared utility functions for the Music Lyrics Processing Pipeline.

This module provides essential utility functions used throughout the pipeline
for file operations, path management, data validation, and configuration.
For comprehensive documentation, see: docs/modules/utils.md

Core Functionality Areas:
- File System Operations (discovery, path management, I/O)
- Data Processing (parsing, conversion, validation)
- Configuration Management (environment variables, API settings)
- Output Management (CSV generation, directory handling)
- Content Processing (LRC/transcript manipulation)

Dependencies:
- pathlib (modern path handling)
- typing (type hints)
- logging_config (pipeline logging)
- csv (CSV file generation)

Used By: All pipeline modules for shared functionality
"""

from pathlib import Path
from typing import List, Dict, Optional
from types import SimpleNamespace
import os

from logging_config import get_logger


logger = get_logger(__name__)


def find_audio_files(input_dir: str) -> List[Path]:
    """
    Find all audio files (FLAC and MP3) in the input directory recursively.

    Args:
        input_dir (str): Directory to search for audio files

    Returns:
        List[Path]: List of audio file paths found (FLAC and MP3)
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return []

    # Find both FLAC and MP3 files
    audio_extensions = ['*.flac', '*.mp3']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(input_path.rglob(ext)))

    logger.info(f"Found {len(audio_files)} audio files ({', '.join(ext[1:] for ext in audio_extensions)}) in {input_dir}")
    return audio_files


def find_flac_files(input_dir: str) -> List[Path]:
    """
    Find all FLAC files in the input directory recursively.

    Args:
        input_dir (str): Directory to search for FLAC files

    Returns:
        List[Path]: List of FLAC file paths found
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return []

    flac_files = list(input_path.rglob("*.flac"))
    logger.info(f"Found {len(flac_files)} FLAC files in {input_dir}")
    return flac_files


def get_output_paths(input_file: Path, output_dir: str = "output", temp_dir: str = "tmp", input_base_dir: str = "input") -> dict:
    """
    Generate output file paths based on the input file path, preserving nested folder structure.
    Creates a song-specific folder within the temp directory to organize all intermediate files.

    Args:
        input_file (Path): Input FLAC file path
        output_dir (str): Output directory for final LRC files
        temp_dir (str): Temporary directory for intermediate files
        input_base_dir (str): Base input directory to calculate relative path from

    Returns:
        dict: Dictionary containing all output file paths
    """
    output_path = Path(output_dir)
    temp_path = Path(temp_dir)
    input_base_path = Path(input_base_dir)
    filename_stem = input_file.stem

    # Calculate relative path from input base directory to preserve folder structure
    try:
        relative_path = input_file.relative_to(input_base_path)
        # Get the parent directory path (without the filename)
        relative_parent = relative_path.parent

        # Create nested directory structure in both temp and output directories
        nested_temp_path = temp_path / relative_parent
        nested_output_path = output_path / relative_parent

        # Create song-specific folder within the nested temp directory
        song_folder = nested_temp_path / filename_stem
        song_folder.mkdir(parents=True, exist_ok=True)

        # Ensure nested directories exist
        nested_output_path.mkdir(parents=True, exist_ok=True)

    except ValueError:
        # If input_file is not relative to input_base_dir, use flat structure
        logger.warning(f"Input file {input_file} is not relative to {input_base_dir}, using flat structure")
        nested_temp_path = temp_path
        nested_output_path = output_path

        # Create song-specific folder within the temp directory
        song_folder = nested_temp_path / filename_stem
        song_folder.mkdir(parents=True, exist_ok=True)

    return {
        'vocals_wav': song_folder / f"{filename_stem}_(Vocals)_UVR_MDXNET_Main.wav",
        'transcript_txt': song_folder / f"{filename_stem}_(Vocals)_UVR_MDXNET_Main_transcript.txt",
        'corrected_transcript_txt': song_folder / f"{filename_stem}_(Vocals)_UVR_MDXNET_Main_corrected_transcript.txt",
        'lyrics_txt': song_folder / f"{filename_stem}_lyrics.txt",
        'lrc': song_folder / f"{filename_stem}.lrc",
        'translated_lrc': nested_output_path / f"{filename_stem}.lrc"
    }


def ensure_output_directory(output_dir: str) -> bool:
    """
    Create output directory if it doesn't exist.

    Args:
        output_dir (str): Output directory path

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return False


def load_prompt_template(prompt_file_path: str) -> str | None:
    """
    Load prompt template from file.

    Args:
        prompt_file_path (str): Path to the prompt template file

    Returns:
        str | None: Content of the prompt template file, or None if error occurred
    """
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt template from {prompt_file_path}: {e}")
        return None


def read_lrc_file(file_path: str) -> str:
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


def read_lyrics_file(file_path: str) -> str:
    """
    Read the downloaded lyrics from file.

    Args:
        file_path (str): Path to the lyrics file

    Returns:
        str: Content of the lyrics file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_transcript_file(file_path: str) -> str:
    """
    Read the ASR transcript from file.

    Args:
        file_path (str): Path to the transcript file

    Returns:
        str: Content of the transcript file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def validate_lrc_content(content: str) -> bool:
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
    import re
    timestamp_pattern = r'\[([0-9]{2,3}:[0-9]{2}\.[0-9]{2,3}|[0-9]{2,3}:[0-9]{2})\]'
    has_timestamps = any(re.search(timestamp_pattern, line) for line in lines)

    if not has_timestamps:
        logger.warning("LRC content doesn't contain any timestamp patterns")
        return False

    # Additional validation could be added here
    logger.info("LRC content validation passed")
    return True


def convert_transcript_to_lrc(transcript_text: str) -> str:
    """
    Convert the ASR transcript to LRC format for better alignment.

    Args:
        transcript_text (str): ASR transcript with timestamps

    Returns:
        str: Transcript in LRC format
    """
    import re
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


def parse_transcript_segments(transcript_content: str) -> List[SimpleNamespace]:
    """
    Parse transcript content back to segments format.

    Args:
        transcript_content (str): Transcript content with timestamp format

    Returns:
        List[SimpleNamespace]: List of transcript segments with start, end, and text
    """
    import re
    lines = transcript_content.split('\n')
    segments = []

    for line in lines:
        # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
        match = re.match(r'\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)', line.strip())
        if match:
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            text = match.group(3).strip()
            segment = SimpleNamespace(start=start_time, end=end_time, text=text)
            segments.append(segment)

    return segments


def should_skip_file(paths: dict, resume: bool) -> bool:
    """
    Check if essential output files already exist and should be skipped.

    Args:
        paths (dict): Dictionary of file paths to check
        resume (bool): Whether resume mode is enabled

    Returns:
        bool: True if essential files exist and should be skipped, False otherwise
    """
    from pathlib import Path

    if not resume:
        return False

    # Only check for essential output files that should always exist when processing is complete
    # Skip optional intermediate files like corrected_transcript_txt which may not be created
    essential_files = [
        paths['translated_lrc'],  # Final output file
        paths['lrc']             # Intermediate LRC file before translation
    ]

    return all(Path(path).exists() for path in essential_files)


def extract_lyrics_content(lyrics_content: str) -> str:
    """
    Extract actual lyrics content from lyrics file format.

    Args:
        lyrics_content (str): Raw lyrics content from file

    Returns:
        str: Extracted lyrics content
    """
    lines = lyrics_content.split('\n')
    lyrics_lines = []

    # Find where actual lyrics start (after headers)
    for i, line in enumerate(lines):
        if line.startswith("=" * 10):  # Start of actual lyrics
            lyrics_lines = lines[i+1:]
            break
    else:
        lyrics_lines = lines[3:]  # Skip title and header lines

    return '\n'.join(lyrics_lines).strip()


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


def write_csv_results(csv_file_path: str, results: list) -> bool:
    """
    Write processing results to CSV file.

    Args:
        csv_file_path (str): Path to the CSV file to write
        results (list): List of result dictionaries to write

    Returns:
        bool: True if writing was successful, False otherwise
    """
    import csv

    if not results:
        logger.warning("No results to write to CSV")
        return False

    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Define CSV columns based on our data structure
            fieldnames = [
                # File information
                'filename', 'file_path', 'processing_start_time',

                # Metadata extraction results
                'metadata_success', 'metadata_title', 'metadata_artist', 'metadata_album',
                'metadata_genre', 'metadata_year', 'metadata_track_number',

                # Vocal separation results
                'vocals_separation_success', 'vocals_file_path', 'vocals_file_size',

                # Transcription results
                'transcription_success', 'transcription_segments_count', 'transcription_duration',

                # Lyrics search results
                'lyrics_search_success', 'lyrics_source', 'lyrics_length', 'lyrics_line_count',

                # Grammatical correction results
                'grammatical_correction_success', 'grammatical_correction_applied',

                # LRC generation results
                'lrc_generation_success', 'lrc_line_count', 'lrc_has_timestamps',

                # Translation results
                'translation_success', 'translation_target_language',

                # Overall results
                'overall_success', 'processing_end_time', 'processing_duration_seconds', 'error_message'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            for result in results:
                writer.writerow(result)

        logger.info(f"CSV results written to: {csv_file_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to write CSV results to {csv_file_path}: {e}")
        return False


def validate_environment_variables(required_vars: List[str], optional_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Validate that required environment variables are set and optionally check optional ones.

    Args:
        required_vars (List[str]): List of required environment variable names
        optional_vars (Optional[Dict[str, str]]): Optional dictionary of variable names to fallback values

    Returns:
        Dict[str, str]: Dictionary of validated environment variables

    Raises:
        ValueError: If any required environment variable is not set
    """
    validated_vars = {}
    missing_vars = []

    # Check required variables
    for var_name in required_vars:
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(var_name)
        else:
            validated_vars[var_name] = value

    # Check optional variables if provided
    if optional_vars:
        for var_name, fallback_value in optional_vars.items():
            value = os.getenv(var_name, fallback_value)
            validated_vars[var_name] = value

    if missing_vars:
        missing_str = ", ".join(missing_vars)
        raise ValueError(f"Missing required environment variables: {missing_str}")

    return validated_vars


def get_openai_config() -> Dict[str, str]:
    """
    Get OpenAI configuration from environment variables with proper validation.

    Returns:
        Dict[str, str]: Dictionary containing base_url, api_key, and model

    Raises:
        ValueError: If required environment variables are not set
    """
    return validate_environment_variables(
        required_vars=["OPENAI_BASE_URL", "OPENAI_API_KEY", "OPENAI_MODEL"]
    )


def get_translation_config() -> Dict[str, str]:
    """
    Get translation configuration from environment variables with fallback support.

    Returns:
        Dict[str, str]: Dictionary containing base_url, api_key, and model for translation

    Raises:
        ValueError: If required environment variables are not set
    """
    # Try translation-specific variables first, fall back to general OpenAI variables
    config = {}

    # Check for translation-specific base URL
    base_url = os.getenv("TRANSLATION_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    if not base_url:
        raise ValueError("Base URL not set (TRANSLATION_BASE_URL or OPENAI_BASE_URL)")

    # Check for translation-specific API key
    api_key = os.getenv("TRANSLATION_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not set (TRANSLATION_API_KEY or OPENAI_API_KEY)")

    # Check for translation-specific model
    model = os.getenv("TRANSLATION_MODEL") or os.getenv("OPENAI_MODEL")
    if not model:
        raise ValueError("Model not set (TRANSLATION_MODEL or OPENAI_MODEL)")

    config["base_url"] = base_url
    config["api_key"] = api_key
    config["model"] = model

    return config

