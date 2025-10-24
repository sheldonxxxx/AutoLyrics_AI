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
import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from types import SimpleNamespace
from datetime import datetime
import time
from pydantic import BaseModel, Field

from logging_config import get_logger

logger = get_logger(__name__)


class ProcessingResults(BaseModel):
    """Manages processing results and metadata for a single file."""

    # File information
    filename: str = Field(description="Name of the input file")
    file_path: str = Field(description="Full path to the input file")
    target_language: str = Field(default="", description="Target language")
    song_language: str = Field(
        default="", description="Language of the song (e.g., Japanese)"
    )
    processing_start_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO timestamp when processing started",
    )
    start_time: float = Field(
        description="Start time in seconds for duration calculation"
    )

    # Step results
    metadata_success: bool = Field(
        default=False, description="Whether metadata extraction succeeded"
    )
    metadata_title: str = Field(default="", description="Song title from metadata")
    metadata_artist: str = Field(default="", description="Artist name from metadata")
    metadata_album: str = Field(default="", description="Album name from metadata")
    metadata_genre: str = Field(default="", description="Genre from metadata")
    metadata_year: str = Field(default="", description="Year from metadata")
    metadata_track_number: str = Field(
        default="", description="Track number from metadata"
    )

    vocals_separation_success: bool = Field(
        default=False, description="Whether vocal separation succeeded"
    )

    transcription_success: bool = Field(
        default=False, description="Whether transcription succeeded"
    )

    lyrics_search_success: bool = Field(
        default=False, description="Whether lyrics search succeeded"
    )

    # Story search results
    story_search_success: bool = Field(
        default=False, description="Whether story search succeeded"
    )

    lrc_generation_success: bool = Field(
        default=False, description="Whether LRC generation succeeded"
    )

    timestamp_verification_success: bool = Field(
        default=False, description="Whether timestamp verification succeeded"
    )

    translation_success: bool = Field(
        default=False, description="Whether translation succeeded"
    )

    explanation_success: bool = Field(
        default=False, description="Whether explanation succeeded"
    )
    
    song_story_search_success: bool = Field(
        default=False, description="Whether song story search succeeded"
    )

    # Overall results
    overall_success: bool = Field(
        default=False, description="Overall processing success"
    )
    processing_end_time: str = Field(
        default="", description="ISO timestamp when processing ended"
    )
    processing_duration_seconds: float = Field(
        default=0.0, description="Total processing duration in seconds"
    )
    error_message: str = Field(
        default="", description="Error message if processing failed"
    )

    @classmethod
    def create(cls, input_file: Path, start_time: float) -> "ProcessingResults":
        """Create a new ProcessingResults instance with initial values."""
        return cls(
            filename=input_file.name,
            file_path=str(input_file),
            processing_start_time=datetime.now().isoformat(),
            start_time=start_time,
        )

    def finalize(self):
        """Finalize results with timing information."""
        end_time = time.time()
        self.processing_end_time = datetime.now().isoformat()
        self.processing_duration_seconds = end_time - self.start_time


def find_audio_files(input_dir: str) -> List[Path]:
    """
    Find all audio files in the input directory recursively.

    Args:
        input_dir (str): Directory to search for audio files

    Returns:
        List[Path]: List of audio file paths found
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return []

    # Find audio files with common extensions
    audio_extensions = ["*.flac", "*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg", "*.wma"]
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(input_path.rglob(ext)))

    # Filter out macOS resource fork files and other system files starting with '._'
    filtered_audio_files = [f for f in audio_files if not f.name.startswith("._")]

    supported_formats = ", ".join(ext[1:] for ext in audio_extensions)
    logger.info(
        f"Found {len(filtered_audio_files)} audio files ({supported_formats}) in {input_dir} (filtered out {len(audio_files) - len(filtered_audio_files)} system files)"
    )
    return filtered_audio_files


def get_output_paths(
    input_file: Path,
    output_dir: str = "output",
    temp_dir: str = "tmp",
    input_base_dir: str = "input",
) -> dict:
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
        logger.warning(
            f"Input file {input_file} is not relative to {input_base_dir}, using flat structure"
        )
        nested_temp_path = temp_path
        nested_output_path = output_path

        # Create song-specific folder within the temp directory
        song_folder = nested_temp_path / filename_stem
        song_folder.mkdir(parents=True, exist_ok=True)

    return {
        "vocals_wav": song_folder / f"{filename_stem}_vocal.wav",
        "normalized_vocals_wav": song_folder / f"{filename_stem}_vocal_normalized.wav",
        "transcript_txt": song_folder / f"{filename_stem}_transcript.txt",
        "transcript_word_txt": song_folder / f"{filename_stem}_transcript_word.txt",
        "corrected_transcript_txt": song_folder / f"{filename_stem}_corrected_transcript.txt",
        "song_identification": song_folder / f"{filename_stem}_song_identification.json",
        "lyrics_txt": song_folder / f"{filename_stem}_lyrics.txt",
        "lrc": song_folder / f"{filename_stem}.lrc",
        "explanation_txt": song_folder / f"{filename_stem}_explanation.md",
        "song_story": song_folder / f"{filename_stem}_song_story.json",
        "corrected_lrc": song_folder / f"{filename_stem}_corrected.lrc",
        "translated_lrc": nested_output_path / f"{filename_stem}.lrc",
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
        logger.exception(f"Failed to create output directory {output_dir}: {e}")
        return False


def load_prompt_template(prompt_file: str, **kwargs) -> str | None:
    """
    Load prompt template from file and format it with provided keyword arguments.

    Args:
        prompt_file_path (str): Path to the prompt template file
        **kwargs: Keyword arguments for formatting the template

    Returns:
        str | None: Formatted content of the prompt template file, or None if error occurred
    """
    try:
        # Load prompt template from file
        prompt_file_path = os.path.join(
            os.path.dirname(__file__), "prompt", prompt_file
        )
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            template = f.read()
        if kwargs:
            return template.format(**kwargs)
        else:
            return template
    except Exception as e:
        logger.exception(f"Error loading prompt template from {prompt_file_path}: {e}")
        return None


def read_file(file_path: str | Path) -> str:
    """
    Read file and return its content as a string.

    Args:
        file_path (str): Path to the LRC file

    Returns:
        str: Content of the LRC file
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def validate_lrc_content(content: str) -> bool:
    """
    Validate that the LRC content has proper format.

    Args:
        content (str): LRC content to validate

    Returns:
        bool: True if content is valid LRC format, False otherwise
    """
    lines = content.strip().split("\n")

    # Check if we have at least one line
    if not lines or not lines[0].strip():
        logger.exception("LRC content is empty")
        return False

    # Check for proper LRC timestamp format in at least some lines
    timestamp_pattern = r"\[(\d{2,3}:\d{2}\.\d{2,3}|\d{2,3}:\d{2})\]"
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

    lines = transcript_text.split("\n")
    lrc_lines = []

    for line in lines:
        # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
        match = re.match(r"\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)", line.strip())
        if match:
            start_time = float(match.group(1))
            text = match.group(3).strip()

            if text:  # Only add non-empty lines
                # Convert seconds to [mm:ss.xx] format
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                hundredths = int((start_time % 1) * 100)
                lrc_line = f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]{text}"
                lrc_lines.append(lrc_line)

    return "\n".join(lrc_lines)


def parse_transcript_segments(transcript_content: str) -> List[SimpleNamespace]:
    """
    Parse transcript content back to segments format.

    Args:
        transcript_content (str): Transcript content with timestamp format

    Returns:
        List[SimpleNamespace]: List of transcript segments with start, end, and text
    """
    import re

    lines = transcript_content.split("\n")
    segments = []

    for line in lines:
        # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
        match = re.match(r"\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)", line.strip())
        if match:
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            text = match.group(3).strip()
            segment = SimpleNamespace(start=start_time, end=end_time, text=text)
            segments.append(segment)

    return segments


def remove_timestamps_from_transcript(transcript: str) -> str:
    """
    Remove timestamps from ASR transcript to reduce token usage.

    Args:
        transcript (str): ASR transcript with timestamps

    Returns:
        str: Transcript with timestamps removed
    """
    if not transcript:
        return transcript

    # Remove common timestamp patterns:
    # [00:00.00] format, [00:00] format, (00:00.00) format, (00:00) format
    # Also handle formats like 00:00.00 - Word or 00:00 - Word
    patterns = [
        r"\[.*?\]",  # Match anything contained within square brackets
    ]

    cleaned_transcript = transcript
    for pattern in patterns:
        cleaned_transcript = re.sub(pattern, "", cleaned_transcript, flags=re.MULTILINE)

    logger.debug(
        f"Removed timestamps from transcript: {len(transcript)} -> {len(cleaned_transcript)} characters"
    )
    return cleaned_transcript


def get_prompt_file_for_language(target_language: str, task: str) -> str:
    """
    Get the appropriate prompt file name for the target language.

    Args:
        target_language (str): Target language for translation/explanation
        task (str): Task type, either "translation" or "explanation"

    Returns:
        str: Prompt file name for the language
    """
    if task == "explanation":
        # Map language names to explanation prompt file names
        language_prompt_map = {
            "Traditional Chinese": "lrc_explanation_traditional_chinese_prompt.txt",
            # Add more specific language prompts here as they are created
            # "English": "lrc_explanation_english_prompt.txt",
            # "Japanese": "lrc_explanation_japanese_prompt.txt",
        }
        # Use specific prompt if available, otherwise use generic explanation prompt
        return language_prompt_map.get(target_language, "lrc_explanation_prompt.txt")
    else:
        # Map language names to translation prompt file names
        language_prompt_map = {
            "Traditional Chinese": "lrc_traditional_chinese_prompt.txt",
            # Add more specific language prompts here as they are created
            # "English": "lrc_english_prompt.txt",
            # "Japanese": "lrc_japanese_prompt.txt",
        }
        # Use specific prompt if available, otherwise use generic prompt
        return language_prompt_map.get(
            target_language, "lrc_generic_translation_prompt.txt"
        )


def write_csv_results(csv_file_path: str, results: List[ProcessingResults]) -> bool:
    """
    Write processing results to CSV file.

    Args:
        csv_file_path (str): Path to the CSV file to write
        results (List[ProcessingResults]): List of ProcessingResults objects to write

    Returns:
        bool: True if writing was successful, False otherwise
    """
    import csv

    if not results:
        logger.warning("No results to write to CSV")
        return False

    try:
        with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
            # Extract fieldnames dynamically from the Pydantic model
            fieldnames = list(ProcessingResults.model_fields.keys())

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            for result in results:
                writer.writerow(result.model_dump())

        logger.info(f"CSV results written to: {csv_file_path}")
        return True

    except Exception as e:
        logger.exception(f"Failed to write CSV results to {csv_file_path}: {e}")
        return False


def validate_environment_variables(
    required_vars: List[str], optional_vars: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
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


def get_default_llm_config() -> Dict[str, str]:
    """
    Get API configuration from environment variables with proper validation.

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
    # Try translation-specific variables first, fall back to general API variables
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


def get_default_target_language() -> str:
    """
    Get default target language from environment variable.

    Returns:
        str: Target language from DEFAULT_TARGET_LANGUAGE env var, or "English" if not set
    """
    return os.getenv("DEFAULT_TARGET_LANGUAGE", "English")


def get_base_argparser(
    description: str, search: bool = False
) -> argparse.ArgumentParser:
    """
    Create a base argument parser with common arguments.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """

    parser = argparse.ArgumentParser(
        description=description,
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--logfire",
        action="store_true",
        help="Enable Logfire logging if set",
    )
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="Force recomputation even if output files exist",
    )

    if search:
        parser.add_argument(
            "--max-search-results",
            type=int,
            default=5,
            help="Maximum number of search results to return (default: 5)",
        )

    return parser
