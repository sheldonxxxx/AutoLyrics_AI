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
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
from mutagen.flac import FLACNoHeaderError, FLAC
import logging
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def extract_metadata(file_path):
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
        if file_path.lower().endswith(".flac"):
            # Use mutagen's FLAC class specifically for FLAC files
            audio_file = FLAC(file_path)
            tags = audio_file.tags
        else:
            # Use generic File class for other formats
            audio_file = File(file_path)
            tags = audio_file.tags

        if tags is None:
            # For formats without tags, try to extract from filename
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

        # Define priority order for processing tags to ensure higher priority tags are processed first
        # Create a list of tuples (priority, tag_key, tag_value) to sort by priority
        prioritized_tags = []
        for key, value in tags.items():
            key_lower = key.lower()

            # Define priorities: 0 = highest priority, higher numbers = lower priority
            if key_lower in ["title", "tracktitle", "©nam", "tit2", "tit3", "title"]:
                priority = 10  # Title
            elif key_lower in [
                "artist",
                "albumartist",
                "tpe1",
                "tpe2",
                "©art",
                "aart",
                "tp1",
                "tp2",
            ]:
                priority = 20  # Primary artist tags
            elif key_lower in [
                "composer",
                "band",
                "ensemble",
                "©art",
                "tpe3",
                "tpe4",
                "tcom",
                "text",
            ]:
                priority = 30  # Secondary artist tags (composer, etc.)
            elif key_lower in ["album", "©alb", "talb"]:
                priority = 40  # Album
            elif key_lower in ["genre", "©gen", "tcon", "gnre"]:
                priority = 50  # Genre
            elif key_lower in ["date", "year", "©day", "tdrc", "tyer"]:
                priority = 60  # Year/Date
            elif key_lower in ["tracknumber", "track", "©trk", "trck"]:
                priority = 70  # Track number
            else:
                priority = 80  # Other tags (lowest priority)

            prioritized_tags.append((priority, key_lower, value))

        # Sort by priority (lower number = higher priority)
        prioritized_tags.sort(key=lambda x: x[0])

        # Process tags in priority order
        for priority, key_lower, value in prioritized_tags:
            # Title fields
            if key_lower in ["title", "tracktitle", "©nam", "tit2", "tit3", "title"]:
                if metadata["title"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["title"] = extracted_value

            # Artist fields - prioritize main artist tags
            elif key_lower in [
                "artist",
                "albumartist",
                "tpe1",
                "tpe2",
                "©art",
                "aart",
                "tp1",
                "tp2",
            ]:
                if metadata["artist"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["artist"] = extracted_value

            # Secondary artist fields (composer, etc.) - only if no primary artist found
            elif key_lower in [
                "composer",
                "band",
                "ensemble",
                "©art",
                "tpe3",
                "tpe4",
                "tcom",
                "text",
            ]:
                if metadata["artist"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["artist"] = extracted_value

            # Album fields
            elif key_lower in ["album", "©alb", "talb"]:
                if metadata["album"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["album"] = extracted_value

            # Genre fields
            elif key_lower in ["genre", "©gen", "tcon", "gnre"]:
                if metadata["genre"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["genre"] = extracted_value

            # Year/Date fields
            elif key_lower in ["date", "year", "©day", "tdrc", "tyer"]:
                if metadata["year"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["year"] = extracted_value

            # Track number fields
            elif key_lower in ["tracknumber", "track", "©trk", "trck"]:
                if metadata["track_number"] is None:
                    # Handle both single values and lists - if it's a list with elements, take the first one
                    extracted_value = (
                        str(value[0])
                        if isinstance(value, list) and len(value) > 0
                        else str(value)
                    )
                    if (
                        extracted_value and extracted_value.strip()
                    ):  # Check if value is not None, empty, or just whitespace
                        metadata["track_number"] = extracted_value

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

    # Set up argument parser
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract song name and artist name from audio file metadata."
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        default="input/0017480280.flac",
        help="Path to the audio file to extract metadata from",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--logfire", action="store_true", help="Enable Logfire integration"
    )

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Define the input file path
    input_file = args.file_path

    # Check if the input file exists
    if not os.path.exists(input_file):
        logger.exception(f"Input file does not exist: {input_file}")
        return

    logger.info(f"Extracting metadata from: {input_file}")

    # Extract metadata
    metadata = extract_metadata(input_file)

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
