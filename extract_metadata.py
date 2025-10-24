#!/usr/bin/env python3
"""
Extract song metadata from audio files.

This module handles metadata extraction for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/extract_metadata.md

Key Features:
- Multiple audio format support (FLAC, MP3, M4A, etc.)
- Intelligent tag priority system
- Filename fallback for missing metadata
- Comprehensive error handling

Dependencies:
- mutagen>=1.47.0
- logging_config (pipeline logging)

Pipeline Stage: 1/6 (Metadata Extraction)
"""

import os
from pathlib import Path

from mutagen import File
from mutagen.id3 import ID3NoHeaderError
from mutagen.flac import FLACNoHeaderError, FLAC

import logging
from logging_config import setup_logging, get_logger
from utils import get_base_argparser

logger = get_logger(__name__)


def extract_and_validate_value(value):
    """
    Extract and validate a metadata value, handling lists, None, and empty values.

    Args:
        value: The raw value from metadata tags

    Returns:
        str or None: The extracted string value if valid, else None
    """
    if value is None:
        return None
    if isinstance(value, list):
        if len(value) > 0 and value[0] is not None:
            extracted = str(value[0]).strip()
            return extracted if extracted else None
        return None
    else:
        extracted = str(value).strip()
        return extracted if extracted else None


def update_metadata_field_if_none(metadata: dict, field: str, value) -> None:
    """
    Update a metadata field if it is currently None.

    Args:
        metadata (dict): The metadata dictionary to update
        field (str): The field name to update
        value: The raw value to extract and validate
    """
    if metadata[field] is None:
        extracted_value = extract_and_validate_value(value)
        if extracted_value:
            metadata[field] = extracted_value


# Priority map for tag keys to reduce cognitive complexity
PRIORITY_MAP = {
    # Title tags (priority 10)
    "title": 10, "tracktitle": 10, "©nam": 10, "tit2": 10, "tit3": 10,
    # Primary artist tags (priority 20)
    "artist": 20, "albumartist": 20, "tpe1": 20, "tpe2": 20, "©art": 20,
    "aart": 20, "tp1": 20, "tp2": 20,
    # Secondary artist tags (priority 30)
    "composer": 30, "band": 30, "ensemble": 30, "tpe3": 30, "tpe4": 30,
    "tcom": 30, "text": 30,
    # Album tags (priority 40)
    "album": 40, "©alb": 40, "talb": 40,
    # Genre tags (priority 50)
    "genre": 50, "©gen": 50, "tcon": 50, "gnre": 50,
    # Year/Date tags (priority 60)
    "date": 60, "year": 60, "©day": 60, "tdrc": 60, "tyer": 60,
    # Track number tags (priority 70)
    "tracknumber": 70, "track": 70, "©trk": 70, "trck": 70,
    # Other tags (priority 80)
}


def update_title(metadata: dict, value) -> None:
    """Update title field if None."""
    update_metadata_field_if_none(metadata, "title", value)


def update_artist(metadata: dict, value) -> None:
    """Update artist field if None."""
    update_metadata_field_if_none(metadata, "artist", value)


def update_album(metadata: dict, value) -> None:
    """Update album field if None."""
    update_metadata_field_if_none(metadata, "album", value)


def update_genre(metadata: dict, value) -> None:
    """Update genre field if None."""
    update_metadata_field_if_none(metadata, "genre", value)


def update_year(metadata: dict, value) -> None:
    """Update year field if None."""
    update_metadata_field_if_none(metadata, "year", value)


def update_track_number(metadata: dict, value) -> None:
    """Update track_number field if None."""
    update_metadata_field_if_none(metadata, "track_number", value)


# Mapping of tag keys to update functions
UPDATE_FUNCTIONS = {
    # Title
    "title": update_title, "tracktitle": update_title, "©nam": update_title,
    "tit2": update_title, "tit3": update_title,
    # Artist (primary and secondary)
    "artist": update_artist, "albumartist": update_artist, "tpe1": update_artist,
    "tpe2": update_artist, "©art": update_artist, "aart": update_artist,
    "tp1": update_artist, "tp2": update_artist, "composer": update_artist,
    "band": update_artist, "ensemble": update_artist, "tpe3": update_artist,
    "tpe4": update_artist, "tcom": update_artist, "text": update_artist,
    # Album
    "album": update_album, "©alb": update_album, "talb": update_album,
    # Genre
    "genre": update_genre, "©gen": update_genre, "tcon": update_genre, "gnre": update_genre,
    # Year
    "date": update_year, "year": update_year, "©day": update_year, "tdrc": update_year, "tyer": update_year,
    # Track number
    "tracknumber": update_track_number, "track": update_track_number, "©trk": update_track_number, "trck": update_track_number,
}


def load_audio_file(file_path: str):
    """
    Load audio file and extract tags based on file type.

    Args:
        file_path (str): Path to the audio file

    Returns:
        tuple: (audio_file, tags) where tags may be None
    """
    if file_path.lower().endswith(".flac"):
        # Use mutagen's FLAC class specifically for FLAC files
        audio_file = FLAC(file_path)
        tags = audio_file.tags
    else:
        # Use generic File class for other formats
        audio_file = File(file_path)
        tags = audio_file.tags

    return audio_file, tags


def parse_filename_for_metadata(file_path: str, metadata: dict) -> dict:
    """
    Parse filename to extract metadata when no tags are available.

    Args:
        file_path (str): Path to the audio file
        metadata (dict): Current metadata dictionary

    Returns:
        dict: Updated metadata dictionary
    """
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]

    # Try to extract artist and title from filename like "Artist - Title"
    if " - " in name_without_ext:
        parts = name_without_ext.split(" - ", 1)
        if len(parts) >= 2:
            metadata["artist"] = parts[0].strip()
            metadata["title"] = parts[1].strip()
    else:
        metadata["title"] = name_without_ext

    return metadata


def process_tags_with_priority(tags: dict, metadata: dict) -> None:
    """
    Process tags in priority order using update functions.

    Args:
        tags (dict): Raw tags from audio file
        metadata (dict): Metadata dictionary to update
    """
    # Create prioritized list of tags based on priority map
    prioritized_tags = []
    for key, value in tags.items():
        key_lower = key.lower()
        priority = PRIORITY_MAP.get(key_lower, 80)  # Default to 80 for unknown tags
        prioritized_tags.append((priority, key_lower, value))

    # Sort by priority (lower number = higher priority)
    prioritized_tags.sort(key=lambda x: x[0])

    # Process tags in priority order using update functions
    for priority, key_lower, value in prioritized_tags:
        update_func = UPDATE_FUNCTIONS.get(key_lower)
        if update_func:
            update_func(metadata, value)


def extract_metadata(file_path: str) -> dict:
    """
    Extract song name and artist from audio file metadata.

    Args:
        file_path (str): Path to the audio file

    Returns:
        dict: Dictionary containing song metadata
    """
    metadata = {
        "title": None,
        "artist": None,
        "album": None,
        "genre": None,
        "year": None,
        "track_number": None,
    }

    try:
        _, tags = load_audio_file(file_path)

        if tags is None:
            return parse_filename_for_metadata(file_path, metadata)

        process_tags_with_priority(tags, metadata)

    except ID3NoHeaderError:
        logger.warning(f"No ID3 header found in {file_path}")
    except FLACNoHeaderError:
        logger.warning(f"No FLAC header found in {file_path}")
    except Exception as e:
        logger.exception(f"Error reading metadata from {file_path}: {e}")

    return metadata


def main():
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    parser = get_base_argparser(
        description="Extract song name and artist name from audio file metadata."
    )

    parser.add_argument(
        "file_path",
        nargs="?",
        default="input/0017480280.flac",
        help="Path to the audio file to extract metadata from",
    )

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Define the input file path
    input_file = Path(args.file_path)

    # Check if the input file exists
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return

    logger.info(f"Extracting metadata from: {input_file}")

    # Extract metadata
    metadata = extract_metadata(str(input_file))

    # Print the extracted metadata
    logger.info("Extracted Metadata:")
    logger.info(f"Title: {metadata['title']}")
    logger.info(f"Artist: {metadata['artist']}")
    logger.info(f"Album: {metadata['album']}")
    logger.info(f"Genre: {metadata['genre']}")
    logger.info(f"Year: {metadata['year']}")
    logger.info(f"Track Number: {metadata['track_number']}")


if __name__ == "__main__":
    main()
