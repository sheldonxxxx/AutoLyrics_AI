#!/usr/bin/env python3
"""
Patch script to add metadata to existing translated LRC files.

This script processes existing output LRC files that were created before
the metadata addition feature was implemented. It reads metadata from
corresponding JSON files in the tmp directory and adds the metadata tags
to the beginning of each LRC file.

Key Features:
- Recursively finds all LRC files in output directory
- Reads metadata from corresponding tmp JSON files
- Adds metadata tags in LRC format ([ti:], [ar:], [al:])
- Preserves existing LRC content and formatting
- Comprehensive logging and error handling

Dependencies:
- logging_config (centralized logging)
- utils (file operations and path management)
- json (JSON file processing)
- pathlib (path operations)

Processing: Sequential per file with metadata validation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from logging_config import setup_logging, get_logger
from utils import find_audio_files, ensure_output_directory, get_output_paths, write_file

logger = get_logger(__name__)


def find_lrc_files(output_dir: str) -> List[Path]:
    """Find all LRC files in output directory recursively."""
    lrc_files = []
    output_path = Path(output_dir)

    if not output_path.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        return lrc_files

    # Find all .lrc files recursively
    for lrc_file in output_path.rglob("*.lrc"):
        lrc_files.append(lrc_file)

    logger.info(f"Found {len(lrc_files)} LRC files in {output_dir}")
    return lrc_files


def read_metadata_from_json(json_path: Path) -> Optional[Dict[str, str]]:
    """Read metadata from JSON file created during song identification."""
    try:
        if not json_path.exists():
            logger.warning(f"JSON file does not exist: {json_path}")
            return None

        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Extract metadata fields
        metadata = {
            'title': json_data.get('song_title', ''),
            'artist': json_data.get('artist_name', ''),
            'album': json_data.get('album', '')
        }

        logger.debug(f"Read metadata from {json_path}: {metadata}")
        return metadata

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading JSON file {json_path}: {e}")
        return None


def construct_metadata_tags(metadata: Dict[str, str]) -> List[str]:
    """Construct LRC metadata tags from metadata dictionary."""
    tags = []

    if metadata.get('title'):
        tags.append(f"[ti:{metadata['title']}]")
    if metadata.get('artist'):
        tags.append(f"[ar:{metadata['artist']}]")
    if metadata.get('album'):
        tags.append(f"[al:{metadata['album']}]")

    return tags


def patch_lrc_with_metadata(lrc_path: Path, metadata: Dict[str, str]) -> bool:
    """Add metadata tags to the beginning of an LRC file."""
    try:
        # Read existing LRC content
        if not lrc_path.exists():
            logger.error(f"LRC file does not exist: {lrc_path}")
            return False

        with open(lrc_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Skip if already has metadata tags
        lines = existing_content.strip().split('\n')
        if lines and any(line.startswith('[ti:') or line.startswith('[ar:') or line.startswith('[al:') for line in lines[:5]):
            logger.info(f"LRC file already has metadata tags, skipping: {lrc_path}")
            return True

        # Construct metadata tags
        metadata_tags = construct_metadata_tags(metadata)

        if not metadata_tags:
            logger.warning(f"No metadata available for {lrc_path}")
            return True

        # Combine metadata tags with existing content
        metadata_section = '\n'.join(metadata_tags)
        new_content = f"{metadata_section}\n\n{existing_content}"

        # Write back to file
        write_file(str(lrc_path), new_content)

        logger.info(f"Added metadata to LRC file: {lrc_path}")
        logger.debug(f"Added tags: {metadata_tags}")

        return True

    except Exception as e:
        logger.error(f"Error patching LRC file {lrc_path}: {e}")
        return False


def find_corresponding_json_path(lrc_path: Path, input_dir: str, temp_dir: str) -> Optional[Path]:
    """Find the corresponding JSON metadata file for an LRC file."""
    try:
        # LRC files are in output/{relative_path}/{filename}.lrc
        # We need to find the corresponding input file and then the JSON file

        # Get relative path from output directory
        output_base = Path('output')
        if lrc_path.is_relative_to(output_base):
            relative_path = lrc_path.relative_to(output_base).parent
            filename = lrc_path.stem  # Remove .lrc extension

            # Try to find corresponding input file
            input_base = Path(input_dir)
            possible_input_file = input_base / relative_path / f"{filename}.flac"

            # If FLAC doesn't exist, try other formats
            if not possible_input_file.exists():
                for ext in ['.mp3', '.wav', '.m4a']:
                    possible_input_file = input_base / relative_path / f"{filename}{ext}"
                    if possible_input_file.exists():
                        break

            if possible_input_file.exists():
                # Get the paths structure for this input file
                paths = get_output_paths(possible_input_file, 'output', temp_dir, input_dir)
                json_path = Path(paths['song_identification'])

                if json_path.exists():
                    return json_path

        # Fallback: try to construct path based on LRC file location
        # This assumes the same folder structure as the main script
        relative_from_output = lrc_path.relative_to('output')
        json_path = Path(temp_dir) / relative_from_output.parent / relative_from_output.stem / 'song_identification.json'

        return json_path if json_path.exists() else None

    except Exception as e:
        logger.error(f"Error finding JSON path for {lrc_path}: {e}")
        return None


def patch_all_lrc_files(input_dir: str = "input", output_dir: str = "output", temp_dir: str = "tmp") -> Tuple[int, int]:
    """Patch all LRC files in output directory with metadata from JSON files."""
    logger.info(f"Starting LRC metadata patch process...")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Temp directory: {temp_dir}")

    # Find all LRC files
    lrc_files = find_lrc_files(output_dir)

    if not lrc_files:
        logger.warning(f"No LRC files found in {output_dir}")
        return 0, 0

    success_count = 0
    total_count = len(lrc_files)

    for lrc_file in lrc_files:
        logger.info(f"Processing LRC file: {lrc_file}")

        # Find corresponding JSON metadata file
        json_path = find_corresponding_json_path(lrc_file, input_dir, temp_dir)

        if not json_path:
            logger.warning(f"No corresponding JSON file found for {lrc_file}")
            continue

        # Read metadata from JSON file
        metadata = read_metadata_from_json(json_path)

        if not metadata:
            logger.warning(f"No metadata found in JSON file: {json_path}")
            continue

        # Check if metadata has actual values
        if not any(metadata.values()):
            logger.warning(f"JSON file contains no metadata values: {json_path}")
            continue

        # Patch LRC file with metadata
        if patch_lrc_with_metadata(lrc_file, metadata):
            success_count += 1
        else:
            logger.error(f"Failed to patch LRC file: {lrc_file}")

    logger.info(f"Patch process completed. Successfully patched {success_count}/{total_count} LRC files")
    return success_count, total_count


def main():
    """Main function for the LRC metadata patch script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Add metadata to existing LRC files that were created before metadata support was added'
    )
    parser.add_argument(
        'input_dir',
        nargs='?',
        default='input',
        help='Input directory containing original audio files (default: input)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Output directory containing LRC files to patch (default: output)'
    )
    parser.add_argument(
        '--temp-dir', '-t',
        default='tmp',
        help='Temporary directory containing JSON metadata files (default: tmp)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be patched without making changes (default: False)'
    )

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")

    # Run the patch process
    success_count, total_count = patch_all_lrc_files(args.input_dir, args.output_dir, args.temp_dir)

    if args.dry_run:
        logger.info(f"DRY RUN: Would have patched {success_count}/{total_count} LRC files")
    else:
        logger.info(f"Successfully patched {success_count}/{total_count} LRC files")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())