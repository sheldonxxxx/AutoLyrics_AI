#!/usr/bin/env python3
"""
Utility functions for the music lyric processing pipeline.
"""

from pathlib import Path
from typing import List

from logging_config import get_logger


logger = get_logger(__name__)


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


def get_output_paths(input_file: Path, output_dir: str = "output", temp_dir: str = "tmp") -> dict:
    """
    Generate output file paths based on the input file path.
    
    Args:
        input_file (Path): Input FLAC file path
        output_dir (str): Output directory for final LRC files
        temp_dir (str): Temporary directory for intermediate files
        
    Returns:
        dict: Dictionary containing all output file paths
    """
    output_path = Path(output_dir)
    temp_path = Path(temp_dir)
    filename_stem = input_file.stem
    
    return {
        'vocals_wav': temp_path / f"{filename_stem}_(Vocals)_UVR_MDXNET_Main.wav",
        'transcript_txt': temp_path / f"{filename_stem}_(Vocals)_UVR_MDXNET_Main_transcript.txt",
        'lyrics_txt': temp_path / f"{filename_stem}_lyrics.txt",
        'lrc': temp_path / f"{filename_stem}.lrc",
        'translated_lrc': output_path / f"{filename_stem}.lrc"
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

