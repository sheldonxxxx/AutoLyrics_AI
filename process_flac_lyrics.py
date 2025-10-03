#!/usr/bin/env python3
"""
Script to process all FLAC files in a folder (recursive) and create LRC files by:
1. Using UVR to separate vocals
2. Using ASR to transcribe vocals with timestamps
3. Searching for lyrics online
4. Generating LRC files with synchronized timestamps
5. Adding translation to Traditional Chinese

This script orchestrates the full workflow in a single command.
"""

import os
import sys
from pathlib import Path
import logging
import argparse
import csv
import time
from datetime import datetime

from logging_config import setup_logging, get_logger
from extract_metadata import extract_metadata
from search_lyrics import search_uta_net
from separate_vocals import separate_vocals, transcribe_with_timestamps
from generate_lrc import read_lyrics_file, read_transcript_file, generate_lrc_lyrics
from translate_lrc import main as translate_main
from openai import OpenAI
from dotenv import load_dotenv
from utils import find_flac_files, ensure_output_directory, get_output_paths

logger = get_logger(__name__)

def write_csv_results(csv_file_path: str, results: list) -> bool:
    """
    Write processing results to CSV file.

    Args:
        csv_file_path (str): Path to the CSV file to write
        results (list): List of result dictionaries to write

    Returns:
        bool: True if writing was successful, False otherwise
    """
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

def process_single_flac_file(
    input_file: Path,
    output_dir: str = "output",
    temp_dir: str = "tmp",
    resume: bool = True,
    log_level: int = logging.INFO
) -> tuple[bool, dict]:
    """
    Process a single FLAC file through the entire workflow.

    Args:
        input_file (Path): Input FLAC file path
        output_dir (str): Output directory for final LRC files
        temp_dir (str): Temporary directory for intermediate files
        resume (bool): Whether to resume processing by skipping files that already have output
        log_level (int): Logging level for the process

    Returns:
        tuple[bool, dict]: (success_status, results_dict) where results_dict contains
                          detailed information about each processing step
    """
    # Initialize results tracking
    start_time = time.time()
    processing_start_time = datetime.now().isoformat()

    results = {
        # File information
        'filename': input_file.name,
        'file_path': str(input_file),
        'processing_start_time': processing_start_time,

        # Metadata extraction results
        'metadata_success': False,
        'metadata_title': '',
        'metadata_artist': '',
        'metadata_album': '',
        'metadata_genre': '',
        'metadata_year': '',
        'metadata_track_number': '',

        # Vocal separation results
        'vocals_separation_success': False,
        'vocals_file_path': '',
        'vocals_file_size': 0,

        # Transcription results
        'transcription_success': False,
        'transcription_segments_count': 0,
        'transcription_duration': 0.0,

        # Lyrics search results
        'lyrics_search_success': False,
        'lyrics_source': '',
        'lyrics_length': 0,
        'lyrics_line_count': 0,

        # LRC generation results
        'lrc_generation_success': False,
        'lrc_line_count': 0,
        'lrc_has_timestamps': False,

        # Translation results
        'translation_success': False,
        'translation_target_language': 'Traditional Chinese',

        # Overall results
        'overall_success': False,
        'processing_end_time': '',
        'processing_duration_seconds': 0.0,
        'error_message': ''
    }

    logger.info(f"Processing file: {input_file}")

    # Get output file paths
    paths = get_output_paths(input_file, output_dir, temp_dir)
    
    # Create temp directory if it doesn't exist
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    
    # Check if all outputs already exist and skip if requested
    if resume and all(path.exists() for path in paths.values()):
        logger.info(f"All output files already exist for {input_file}, skipping...")
        return True

    try:
        # Step 1: Extract metadata
        logger.info("Step 1: Extracting metadata...")
        try:
            metadata = extract_metadata(str(input_file))
            results['metadata_success'] = True
            results['metadata_title'] = metadata.get('title', '')
            results['metadata_artist'] = metadata.get('artist', '')
            results['metadata_album'] = metadata.get('album', '')
            results['metadata_genre'] = metadata.get('genre', '')
            results['metadata_year'] = str(metadata.get('year', ''))
            results['metadata_track_number'] = str(metadata.get('track_number', ''))
            logger.info(f"Metadata extracted: {metadata.get('title', 'Unknown')} - {metadata.get('artist', 'Unknown')}")

            if not (metadata['title'] and metadata['artist']):
                logger.warning(f"Missing title or artist for {input_file}, cannot search for lyrics")
                # We can still continue with vocal separation and ASR even without lyrics
        except Exception as e:
            results['metadata_success'] = False
            results['error_message'] = f"Metadata extraction failed: {e}"
            logger.error(f"Failed to extract metadata for {input_file}: {e}")
            return False, results

        # Step 2: Separate vocals using UVR (skip if vocals file already exists)
        vocals_path = paths['vocals_wav']
        if resume and vocals_path.exists():
            logger.info(f"Vocals file already exists for {input_file}, skipping vocal separation...")
            vocals_file = str(vocals_path)
            results['vocals_separation_success'] = True
            results['vocals_file_path'] = vocals_file
            if Path(vocals_file).exists():
                results['vocals_file_size'] = Path(vocals_file).stat().st_size
        else:
            logger.info("Step 2: Separating vocals using UVR...")
            try:
                vocals_file = separate_vocals(str(input_file), output_dir=temp_dir)
                if vocals_file and Path(vocals_file).exists():
                    results['vocals_separation_success'] = True
                    results['vocals_file_path'] = vocals_file
                    results['vocals_file_size'] = Path(vocals_file).stat().st_size
                    logger.info(f"Vocals separated successfully: {vocals_file}")
                else:
                    results['vocals_separation_success'] = False
                    results['error_message'] = "Vocal separation returned no file"
                    logger.error(f"Failed to separate vocals for {input_file}")
                    return False, results
            except Exception as e:
                results['vocals_separation_success'] = False
                results['error_message'] = f"Vocal separation failed: {e}"
                logger.error(f"Exception during vocal separation for {input_file}: {e}")
                return False, results

        # Step 3: Transcribe vocals with ASR and timestamps (skip if transcript already exists)
        transcript_path = paths['transcript_txt']
        if resume and transcript_path.exists():
            logger.info(f"ASR transcript already exists for {input_file}, skipping ASR...")
            # Load existing transcript segments
            logger.info("Loading existing ASR transcript...")
            transcript_content = read_transcript_file(str(transcript_path))
            # We need to parse the transcript back to segments format
            import re
            from types import SimpleNamespace
            lines = transcript_content.split('\n')
            parsed_segments = []
            for line in lines:
                # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
                match = re.match(r'\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)', line.strip())
                if match:
                    start_time = float(match.group(1))
                    end_time = float(match.group(2))
                    text = match.group(3).strip()
                    # Create a simple object with start, end, and text attributes
                    segment = SimpleNamespace(start=start_time, end=end_time, text=text)
                    parsed_segments.append(segment)
            segments = parsed_segments
            logger.info(f"Loaded {len(segments)} segments from existing transcript")
        else:
            logger.info("Step 3: Transcribing vocals with ASR...")
            try:
                segments = transcribe_with_timestamps(vocals_file)
                if segments:
                    results['transcription_success'] = True
                    results['transcription_segments_count'] = len(segments)
                    if segments:
                        # Calculate total duration from segments
                        total_duration = max(segment.end for segment in segments) if segments else 0.0
                        results['transcription_duration'] = total_duration

                    # Save transcript to file
                    transcript_file = str(paths['transcript_txt'])
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write("Timestamped Transcription:\n\n")
                        for segment in segments:
                            f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
                    logger.info(f"Transcription completed: {len(segments)} segments, saved to: {transcript_file}")
                else:
                    results['transcription_success'] = False
                    results['error_message'] = "Transcription returned no segments"
                    logger.error(f"Failed to transcribe vocals for {input_file}")
                    return False, results
            except Exception as e:
                results['transcription_success'] = False
                results['error_message'] = f"Transcription failed: {e}"
                logger.error(f"Exception during transcription for {input_file}: {e}")
                return False, results

        # Step 4: Search for lyrics (only if we have title and artist, and lyrics file doesn't exist yet)
        lyrics_content = None
        lyrics_path = paths['lyrics_txt']
        if metadata['title'] and metadata['artist']:
            if resume and lyrics_path.exists():
                logger.info(f"Lyrics file already exists for {input_file}, skipping lyrics search...")
                # Read existing lyrics
                try:
                    with open(lyrics_path, 'r', encoding='utf-8') as f:
                        lyrics_content = f.read()
                    # Extract just the lyrics part (skip header lines)
                    lines = lyrics_content.split('\n')
                    # Find where actual lyrics start (after headers)
                    lyrics_lines = []
                    for i, line in enumerate(lines):
                        if line.startswith("=" * 10):  # Start of actual lyrics
                            lyrics_lines = lines[i+1:]
                            break
                    else:
                        lyrics_lines = lines[3:]  # Skip title and header lines
                    lyrics_content = '\n'.join(lyrics_lines).strip()

                    results['lyrics_search_success'] = True
                    results['lyrics_source'] = 'uta-net.com (cached)'
                    results['lyrics_length'] = len(lyrics_content)
                    results['lyrics_line_count'] = len(lyrics_content.split('\n')) if lyrics_content else 0
                except Exception as e:
                    results['lyrics_search_success'] = False
                    results['error_message'] = f"Failed to read existing lyrics: {e}"
                    logger.error(f"Failed to read existing lyrics for {input_file}: {e}")
            else:
                logger.info("Step 4: Searching for lyrics...")
                try:
                    lyrics_content = search_uta_net(metadata['title'], metadata['artist'])
                    if lyrics_content:
                        results['lyrics_search_success'] = True
                        results['lyrics_source'] = 'uta-net.com'
                        results['lyrics_length'] = len(lyrics_content)
                        results['lyrics_line_count'] = len(lyrics_content.split('\n'))

                        # Save lyrics to file
                        lyrics_file = str(paths['lyrics_txt'])
                        with open(lyrics_file, 'w', encoding='utf-8') as f:
                            f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
                            f.write("=" * 60 + "\n\n")
                            f.write(lyrics_content)
                            f.write(f"\n\nSource: uta-net.com")
                        logger.info(f"Lyrics found and saved: {results['lyrics_length']} chars, {results['lyrics_line_count']} lines")
                    else:
                        results['lyrics_search_success'] = False
                        logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
                except Exception as e:
                    results['lyrics_search_success'] = False
                    results['error_message'] = f"Lyrics search failed: {e}"
                    logger.error(f"Exception during lyrics search for {input_file}: {e}")
        else:
            logger.info("Skipping lyrics search due to missing title or artist metadata")
            results['lyrics_search_success'] = False

        # Step 5: Generate LRC file by combining lyrics and ASR transcript (skip if LRC already exists)
        lrc_path = paths['lrc']
        if resume and lrc_path.exists():
            logger.info(f"LRC file already exists for {input_file}, skipping LRC generation...")
            # Read existing LRC content
            with open(lrc_path, 'r', encoding='utf-8') as f:
                lrc_lyrics = f.read()
        else:
            logger.info("Step 5: Generating LRC file...")
            
            # Initialize OpenAI client
            load_dotenv()
            base_url = os.getenv("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1")
            api_key = os.getenv("OPENAI_API_KEY", "")
            
            if not api_key:
                logger.error("Error: OPENAI_API_KEY environment variable not set")
                return False
            
            client = OpenAI(base_url=base_url, api_key=api_key)
            
            # Read transcript file content
            asr_transcript = read_transcript_file(str(transcript_path))
            
            # If we have lyrics, generate LRC by combining lyrics and ASR transcript
            if lyrics_content:
                lrc_lyrics = generate_lrc_lyrics(client, lyrics_content, asr_transcript)
            else:
                # If no lyrics found, just convert ASR transcript to LRC format
                logger.info("No lyrics found, converting ASR transcript to LRC format...")
                import re
                lines = asr_transcript.split('\n')
                lrc_lines = []
                
                for line in lines:
                    # Match timestamp format like [0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
                    match = re.match(r'\[([\d.]+)s -> ([\d.]+)s\]\s*(.*)', line.strip())
                    if match:
                        start_time = float(match.group(1))
                        text = match.group(3).strip()
                        
                        if text:  # Only add non-empty lines
                            # Convert seconds to [mm:ss.xx] format
                            minutes = int(start_time // 60)
                            seconds = int(start_time % 60)
                            hundredths = int((start_time % 1) * 100)
                            lrc_line = f'[{minutes:02d}:{seconds:02d}.{hundredths:02d}]{text}'
                            lrc_lines.append(lrc_line)
                
                lrc_lyrics = '\n'.join(lrc_lines)
            
            if lrc_lyrics:
                results['lrc_generation_success'] = True
                results['lrc_line_count'] = len(lrc_lyrics.split('\n')) if lrc_lyrics else 0
                # Check if LRC has timestamps (basic check for [mm:ss.xx] format)
                import re
                timestamp_pattern = r'\[\d{2}:\d{2}\.\d{2}\]'
                results['lrc_has_timestamps'] = bool(re.search(timestamp_pattern, lrc_lyrics))

                # Save LRC file
                lrc_file = str(paths['lrc'])
                with open(lrc_file, 'w', encoding='utf-8') as f:
                    f.write(lrc_lyrics)
                logger.info(f"LRC generated: {results['lrc_line_count']} lines, timestamps: {results['lrc_has_timestamps']}")
            else:
                results['lrc_generation_success'] = False
                results['error_message'] = "LRC generation returned no content"
                logger.error(f"Failed to generate LRC for {input_file}")
                return False, results

        # Step 6: Add translation to Traditional Chinese (skip if translated LRC already exists)
        translated_lrc_path = paths['translated_lrc']
        if resume and translated_lrc_path.exists():
            logger.info(f"Translated LRC file already exists for {input_file}, skipping translation...")
            success = True
        else:
            logger.info("Step 6: Adding translation to Traditional Chinese...")
            success = translate_main(
                str(lrc_path),
                str(translated_lrc_path),
                "Traditional Chinese",
                log_level
            )

        if success:
            results['translation_success'] = True
            results['overall_success'] = True
            logger.info(f"Processing completed successfully for {input_file}")
        else:
            results['translation_success'] = False
            results['error_message'] = "Translation failed"
            logger.error(f"Translation failed for {input_file}")

        # Record final timing information
        end_time = time.time()
        results['processing_end_time'] = datetime.now().isoformat()
        results['processing_duration_seconds'] = end_time - start_time

        return results['overall_success'], results

    except Exception as e:
        # Record final timing and error information
        end_time = time.time()
        results['processing_end_time'] = datetime.now().isoformat()
        results['processing_duration_seconds'] = end_time - start_time
        results['overall_success'] = False
        results['error_message'] = str(e)
        logger.error(f"Error processing file {input_file}: {e}")
        return False, results
            


def main():
    """Main function to process all FLAC files in a directory and output results to CSV."""
    parser = argparse.ArgumentParser(
        description='Process all FLAC files in a folder (recursive) to create LRC files with translation. Outputs detailed results to CSV.'
    )
    parser.add_argument(
        'input_dir',
        nargs='?',
        default='input',
        help='Input directory containing FLAC files (default: input)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Output directory for final LRC files (default: output)'
    )
    parser.add_argument(
        '--temp-dir', '-t',
        default='tmp',
        help='Temporary directory for intermediate files (default: tmp)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume processing by skipping files that already have output files (default: False)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--csv-output', '-c',
        default='output/processing_results.csv',
        help='CSV file to save processing results (default: processing_results.csv)'
    )
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)
    
    logger.info(f"Starting FLAC lyric processing for directory: {args.input_dir}")
    
    # Ensure output directory exists
    if not ensure_output_directory(args.output_dir):
        logger.error("Failed to create output directory, exiting...")
        return 1
    
    # Create temporary directory
    Path(args.temp_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temporary directory: {args.temp_dir}")
    
    # Find all FLAC files
    flac_files = find_flac_files(args.input_dir)
    
    if not flac_files:
        logger.warning(f"No FLAC files found in {args.input_dir}")
        return 0
    
    # Process each FLAC file
    success_count = 0
    all_results = []
    for flac_file in flac_files:
        logger.info(f"Processing {flac_file} ({success_count + 1}/{len(flac_files)})")
        success, results = process_single_flac_file(flac_file, args.output_dir, args.temp_dir, args.resume, log_level)
        all_results.append(results)

        if success:
            success_count += 1
        else:
            logger.error(f"Failed to process {flac_file}")

    logger.info(f"Processing completed. Successfully processed {success_count}/{len(flac_files)} files.")

    # Write results to CSV
    logger.info(f"Writing processing results to CSV: {args.csv_output}")
    if write_csv_results(args.csv_output, all_results):
        logger.info(f"CSV file saved successfully with {len(all_results)} records")
    else:
        logger.error("Failed to write CSV file")
    
    return 0 if success_count == len(flac_files) else 1


if __name__ == "__main__":
    sys.exit(main())

