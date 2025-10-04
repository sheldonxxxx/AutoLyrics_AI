#!/usr/bin/env python3
"""
Script to process all audio files (FLAC and MP3) in a folder (recursive) and create LRC files by:
1. Using UVR to separate vocals
2. Using ASR to transcribe vocals with timestamps
3. Searching for lyrics online
4. Applying grammatical correction to ASR transcript (if no lyrics found)
5. Generating LRC files with synchronized timestamps
6. Adding translation to Traditional Chinese

This script orchestrates the full workflow in a single command.
"""

import os
import sys
import re
from pathlib import Path
import logging
import argparse
import csv
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

from logging_config import setup_logging, get_logger
from extract_metadata import extract_metadata
from search_lyrics import search_uta_net
from separate_vocals import separate_vocals
from transcribe_vocals import transcribe_with_timestamps
from generate_lrc import read_lyrics_file, read_transcript_file, generate_lrc_lyrics, correct_grammar_in_transcript
from translate_lrc import main as translate_main
from identify_song import identify_song_from_asr
from openai import OpenAI
from dotenv import load_dotenv
from utils import (
    find_audio_files, ensure_output_directory, get_output_paths,
    parse_transcript_segments, extract_lyrics_content, convert_transcript_to_lrc,
    should_skip_file, write_csv_results, get_openai_config
)

logger = get_logger(__name__)


class ProcessingResults:
    """Manages processing results and metadata for a single file."""

    def __init__(self, input_file: Path, start_time: float):
        self.input_file = input_file
        self.start_time = start_time
        self.processing_start_time = datetime.now().isoformat()

        # File information
        self.filename = input_file.name
        self.file_path = str(input_file)

        # Step results
        self.metadata_success = False
        self.metadata_title = ''
        self.metadata_artist = ''
        self.metadata_album = ''
        self.metadata_genre = ''
        self.metadata_year = ''
        self.metadata_track_number = ''

        self.vocals_separation_success = False
        self.vocals_file_path = ''
        self.vocals_file_size = 0

        self.transcription_success = False
        self.transcription_segments_count = 0
        self.transcription_duration = 0.0

        self.lyrics_search_success = False
        self.lyrics_source = ''
        self.lyrics_length = 0
        self.lyrics_line_count = 0

        self.grammatical_correction_success = False
        self.grammatical_correction_applied = False

        self.lrc_generation_success = False
        self.lrc_line_count = 0
        self.lrc_has_timestamps = False

        self.translation_success = False
        self.translation_target_language = 'Traditional Chinese'

        # Overall results
        self.overall_success = False
        self.processing_end_time = ''
        self.processing_duration_seconds = 0.0
        self.error_message = ''

    def to_dict(self) -> dict:
        """Convert results to dictionary format for CSV export."""
        return {
            'filename': self.filename,
            'file_path': self.file_path,
            'processing_start_time': self.processing_start_time,
            'metadata_success': self.metadata_success,
            'metadata_title': self.metadata_title,
            'metadata_artist': self.metadata_artist,
            'metadata_album': self.metadata_album,
            'metadata_genre': self.metadata_genre,
            'metadata_year': self.metadata_year,
            'metadata_track_number': self.metadata_track_number,
            'vocals_separation_success': self.vocals_separation_success,
            'vocals_file_path': self.vocals_file_path,
            'vocals_file_size': self.vocals_file_size,
            'transcription_success': self.transcription_success,
            'transcription_segments_count': self.transcription_segments_count,
            'transcription_duration': self.transcription_duration,
            'lyrics_search_success': self.lyrics_search_success,
            'lyrics_source': self.lyrics_source,
            'lyrics_length': self.lyrics_length,
            'lyrics_line_count': self.lyrics_line_count,
            'grammatical_correction_success': self.grammatical_correction_success,
            'grammatical_correction_applied': self.grammatical_correction_applied,
            'lrc_generation_success': self.lrc_generation_success,
            'lrc_line_count': self.lrc_line_count,
            'lrc_has_timestamps': self.lrc_has_timestamps,
            'translation_success': self.translation_success,
            'translation_target_language': self.translation_target_language,
            'overall_success': self.overall_success,
            'processing_end_time': self.processing_end_time,
            'processing_duration_seconds': self.processing_duration_seconds,
            'error_message': self.error_message
        }

    def finalize(self):
        """Finalize results with timing information."""
        end_time = time.time()
        self.processing_end_time = datetime.now().isoformat()
        self.processing_duration_seconds = end_time - self.start_time




def extract_metadata_step(input_file: Path, results: ProcessingResults) -> bool:
    """Step 1: Extract metadata from audio file."""
    logger.info("Step 1: Extracting metadata...")

    try:
        metadata = extract_metadata(str(input_file))
        results.metadata_success = True
        results.metadata_title = metadata.get('title', '')
        results.metadata_artist = metadata.get('artist', '')
        results.metadata_album = metadata.get('album', '')
        results.metadata_genre = metadata.get('genre', '')
        results.metadata_year = str(metadata.get('year', ''))
        results.metadata_track_number = str(metadata.get('track_number', ''))
        logger.info(f"Metadata extracted: {metadata.get('title', 'Unknown')} - {metadata.get('artist', 'Unknown')}")

        if not (metadata['title'] and metadata['artist']):
            logger.warning(f"Missing title or artist for {input_file}, cannot search for lyrics")
        return True

    except Exception as e:
        results.metadata_success = False
        results.error_message = f"Metadata extraction failed: {e}"
        logger.error(f"Failed to extract metadata for {input_file}: {e}")
        return False


def separate_vocals_step(input_file: Path, paths: dict, resume: bool, results: ProcessingResults, temp_dir: str = "tmp") -> bool:
    """Step 2: Separate vocals using UVR."""
    vocals_path = paths['vocals_wav']
    
    logger.info("Step 2: Separating vocals using UVR...")

    if resume and vocals_path.exists():
        logger.info(f"Vocals file already exists for {input_file}, skipping vocal separation...")
        vocals_file = str(vocals_path)
        results.vocals_separation_success = True
        results.vocals_file_path = vocals_file
        if Path(vocals_file).exists():
            results.vocals_file_size = Path(vocals_file).stat().st_size
        return True

    try:
        vocals_file = separate_vocals(str(input_file), output_dir=temp_dir, vocals_output_path=str(paths['vocals_wav']))
        if vocals_file and Path(vocals_file).exists():
            results.vocals_separation_success = True
            results.vocals_file_path = vocals_file
            results.vocals_file_size = Path(vocals_file).stat().st_size
            logger.info(f"Vocals separated successfully: {vocals_file}")
            return True
        else:
            results.vocals_separation_success = False
            results.error_message = "Vocal separation returned no file"
            logger.error(f"Failed to separate vocals for {input_file}")
            return False

    except Exception as e:
        results.vocals_separation_success = False
        results.error_message = f"Vocal separation failed: {e}"
        logger.error(f"Exception during vocal separation for {input_file}: {e}")
        return False


def transcribe_vocals_step(vocals_file: str, paths: dict, resume: bool, results: ProcessingResults) -> Optional[List[SimpleNamespace]]:
    """Step 3: Transcribe vocals with ASR and timestamps."""
    transcript_path = paths['transcript_txt']
    
    logger.info("Step 3: Transcribing vocals with ASR...")

    if resume and transcript_path.exists():
        logger.info(f"ASR transcript already exists for {vocals_file}, skipping ASR...")
        logger.info("Loading existing ASR transcript...")
        transcript_content = read_transcript_file(str(transcript_path))
        return parse_transcript_segments(transcript_content)

    try:
        segments = transcribe_with_timestamps(vocals_file)
        if segments:
            results.transcription_success = True
            results.transcription_segments_count = len(segments)
            if segments:
                total_duration = max(segment.end for segment in segments)
                results.transcription_duration = total_duration

            # Save transcript to file
            transcript_file = str(paths['transcript_txt'])
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write("Timestamped Transcription:\n\n")
                for segment in segments:
                    f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
            logger.info(f"Transcription completed: {len(segments)} segments, saved to: {transcript_file}")
            return segments
        else:
            results.transcription_success = False
            results.error_message = "Transcription returned no segments"
            logger.error(f"Failed to transcribe vocals for {vocals_file}")
            return None

    except Exception as e:
        results.transcription_success = False
        results.error_message = f"Transcription failed: {e}"
        logger.error(f"Exception during transcription for {vocals_file}: {e}")
        return None


def search_lyrics_step(metadata: dict, paths: dict, resume: bool, results: ProcessingResults, transcript_content: Optional[str] = None) -> Optional[str]:
    """Step 4: Search for lyrics online."""

    # Check if we have metadata
    has_metadata = metadata['title'] and metadata['artist']

    # If no metadata but we have transcript, try to identify song from ASR
    if not has_metadata and transcript_content:
        logger.info("No metadata available, attempting to identify song from ASR transcript...")

        # Define result file path for song identification caching
        song_id_result_path = paths['transcript_txt'].with_name(f"{results.filename.replace('.', '_')}_song_identification.json")

        identified_song = identify_song_from_asr(transcript_content, str(song_id_result_path), force_recompute=not resume)

        if identified_song:
            song_title, artist_name, native_language = identified_song
            logger.info(f"Successfully identified song from ASR: '{song_title}' by {artist_name} ({native_language})")

            # Update metadata with identified information
            metadata['title'] = song_title
            metadata['artist'] = artist_name
            results.metadata_title = song_title
            results.metadata_artist = artist_name
            has_metadata = True
            results.lyrics_source = f'uta-net.com (identified from ASR: {native_language})'
        else:
            logger.warning("Could not identify song from ASR transcript")
            results.lyrics_search_success = False
            return None

    if not has_metadata:
        logger.info("Skipping lyrics search due to missing title or artist metadata")
        results.lyrics_search_success = False
        return None

    lyrics_path = paths['lyrics_txt']

    if resume and lyrics_path.exists():
        logger.info(f"Lyrics file already exists, skipping lyrics search...")
        try:
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                lyrics_content = f.read()
            lyrics_content = extract_lyrics_content(lyrics_content)
            results.lyrics_search_success = True
            results.lyrics_source = 'uta-net.com (cached)'
            results.lyrics_length = len(lyrics_content)
            results.lyrics_line_count = len(lyrics_content.split('\n')) if lyrics_content else 0
            return lyrics_content
        except Exception as e:
            results.lyrics_search_success = False
            results.error_message = f"Failed to read existing lyrics: {e}"
            logger.error(f"Failed to read existing lyrics: {e}")
            return None

    logger.info("Step 4: Searching for lyrics...")

    try:
        lyrics_content = search_uta_net(metadata['title'], metadata['artist'])
        if lyrics_content:
            results.lyrics_search_success = True
            results.lyrics_source = 'uta-net.com'
            results.lyrics_length = len(lyrics_content)
            results.lyrics_line_count = len(lyrics_content.split('\n'))

            # Save lyrics to file
            lyrics_file = str(paths['lyrics_txt'])
            with open(lyrics_file, 'w', encoding='utf-8') as f:
                f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
                f.write("=" * 60 + "\n\n")
                f.write(lyrics_content)
                f.write(f"\n\nSource: uta-net.com")
            logger.info(f"Lyrics found and saved: {results.lyrics_length} chars, {results.lyrics_line_count} lines")
            return lyrics_content
        else:
            results.lyrics_search_success = False
            logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
            return None

    except Exception as e:
        results.lyrics_search_success = False
        results.error_message = f"Lyrics search failed: {e}"
        logger.error(f"Exception during lyrics search: {e}")
        return None


def grammatical_correction_step(paths: dict, resume: bool, results: ProcessingResults) -> Optional[str]:
    """Step 4.5: Apply grammatical correction to ASR transcript if no lyrics found."""

    corrected_transcript_path = paths['corrected_transcript_txt']

    # Check for existing corrected transcript file when resuming
    if resume and corrected_transcript_path.exists():
        logger.info("Corrected transcript file already exists, skipping grammatical correction...")
        try:
            corrected_content = read_transcript_file(str(corrected_transcript_path))
            results.grammatical_correction_success = True
            results.grammatical_correction_applied = True  # Assume it was applied if file exists
            return corrected_content
        except Exception as e:
            results.grammatical_correction_success = False
            results.error_message = f"Failed to read existing corrected transcript: {e}"
            logger.error(f"Failed to read existing corrected transcript: {e}")
            return None

    logger.info("Step 4.5: Applying grammatical correction to ASR transcript...")

    try:
        # Initialize OpenAI client for grammatical correction
        load_dotenv()
        config = get_openai_config()

        client = OpenAI(base_url=config["OPENAI_BASE_URL"], api_key=config["OPENAI_API_KEY"])

        # Read the ASR transcript for correction
        transcript_path = str(paths['transcript_txt'])
        asr_transcript = read_transcript_file(transcript_path)

        # Apply grammatical correction
        corrected_transcript = correct_grammar_in_transcript(client, asr_transcript, results.filename, config["OPENAI_MODEL"])

        if corrected_transcript and corrected_transcript != asr_transcript:
            results.grammatical_correction_success = True
            results.grammatical_correction_applied = True

            # Save corrected transcript to file for debugging and resume
            corrected_file = str(corrected_transcript_path)
            with open(corrected_file, 'w', encoding='utf-8') as f:
                f.write("Grammatically Corrected Transcription:\n\n")
                f.write(corrected_transcript)
                f.write(f"\n\nSource: Corrected from ASR transcript")

            logger.info(f"Grammatical correction applied successfully and saved to: {corrected_file}")
            return corrected_transcript
        else:
            results.grammatical_correction_success = True
            results.grammatical_correction_applied = False
            logger.info("No grammatical corrections needed or correction failed")
            return None

    except Exception as e:
        results.grammatical_correction_success = False
        results.error_message = f"Grammatical correction failed: {e}"
        logger.error(f"Exception during grammatical correction: {e}")
        return None

def generate_lrc_step(lyrics_content: Optional[str], corrected_transcript_content: Optional[str], transcript_path: str, paths: dict, resume: bool, results: ProcessingResults) -> bool:
    """Step 5: Generate LRC file by combining lyrics and ASR transcript."""
    lrc_path = paths['lrc']
    
    logger.info("Step 5: Generating LRC file...")

    if resume and lrc_path.exists():
        logger.info(f"LRC file already exists, skipping LRC generation...")
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lrc_lyrics = f.read()
    else:
        # Initialize OpenAI client
        load_dotenv()
        config = get_openai_config()

        client = OpenAI(base_url=config["OPENAI_BASE_URL"], api_key=config["OPENAI_API_KEY"])

        # Read transcript file content
        asr_transcript = read_transcript_file(transcript_path)

        # Generate LRC
        if lyrics_content:
            lrc_lyrics = generate_lrc_lyrics(client, lyrics_content, asr_transcript, config["OPENAI_MODEL"])
        elif corrected_transcript_content:
            logger.info("No lyrics found, using grammatically corrected transcript for LRC generation...")
            lrc_lyrics = generate_lrc_lyrics(client, corrected_transcript_content, asr_transcript, config["OPENAI_MODEL"])
        else:
            logger.info("No lyrics found and no corrected transcript, converting ASR transcript to LRC format...")
            lrc_lyrics = convert_transcript_to_lrc(asr_transcript)

        if lrc_lyrics:
            results.lrc_generation_success = True
            results.lrc_line_count = len(lrc_lyrics.split('\n')) if lrc_lyrics else 0
            # Check if LRC has timestamps (basic check for [mm:ss.xx] format)
            timestamp_pattern = r'\[\d{2}:\d{2}\.\d{2}\]'
            results.lrc_has_timestamps = bool(re.search(timestamp_pattern, lrc_lyrics))

            # Save LRC file
            lrc_file = str(paths['lrc'])
            with open(lrc_file, 'w', encoding='utf-8') as f:
                f.write(lrc_lyrics)
            logger.info(f"LRC generated: {results.lrc_line_count} lines, timestamps: {results.lrc_has_timestamps}")
            return True
        else:
            results.lrc_generation_success = False
            results.error_message = "LRC generation returned no content"
            logger.error("Failed to generate LRC")
            return False

    return True


def translate_lrc_step(lrc_path: str, paths: dict, resume: bool, log_level: int, results: ProcessingResults) -> bool:
    """Step 6: Add translation to Traditional Chinese."""
    translated_lrc_path = paths['translated_lrc']

    logger.info("Step 6: Adding translation to Traditional Chinese...")

    if resume and translated_lrc_path.exists():
        logger.info(f"Translated LRC file already exists, skipping translation...")
        return True
    
    success = translate_main(lrc_path, str(translated_lrc_path), "Traditional Chinese", log_level)

    if success:
        results.translation_success = True
        results.overall_success = True
        logger.info("Processing completed successfully")
    else:
        results.translation_success = False
        results.error_message = "Translation failed"
        logger.error("Translation failed")

    return success


def process_single_audio_file(
    input_file: Path,
    output_dir: str = "output",
    temp_dir: str = "tmp",
    resume: bool = True,
    log_level: int = logging.INFO,
    input_dir: str = "input"
) -> Tuple[bool, dict]:
    """
    Process a single audio file (FLAC or MP3) through the entire workflow.

    Args:
        input_file (Path): Input audio file path (FLAC or MP3)
        output_dir (str): Output directory for final LRC files
        temp_dir (str): Temporary directory for intermediate files
        resume (bool): Whether to resume processing by skipping files that already have output
        log_level (int): Logging level for the process

    Returns:
        Tuple[bool, dict]: (success_status, results_dict) where results_dict contains
                          detailed information about each processing step
    """
    start_time = time.time()
    results = ProcessingResults(input_file, start_time)

    logger.info(f"Processing file: {input_file}")

    # Get output file paths (preserving nested folder structure)
    paths = get_output_paths(input_file, output_dir, temp_dir, input_dir)

    # Create temp directory if it doesn't exist
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    # Check if all outputs already exist and skip if requested
    # if should_skip_file(paths, resume):
    #     logger.info(f"All output files already exist for {input_file}, skipping...")
    #     results.finalize()
    #     return True, results.to_dict()

    try:
        # Step 1: Extract metadata
        if not extract_metadata_step(input_file, results):
            results.finalize()
            return False, results.to_dict()

        # Step 2: Separate vocals using UVR
        if not separate_vocals_step(input_file, paths, resume, results, temp_dir):
            results.finalize()
            return False, results.to_dict()

        # Step 3: Transcribe vocals with ASR and timestamps
        segments = transcribe_vocals_step(results.vocals_file_path, paths, resume, results)
        if segments is None:
            results.finalize()
            return False, results.to_dict()

        # Read transcript content for potential song identification
        transcript_path = str(paths['transcript_txt'])
        transcript_content = None
        try:
            transcript_content = read_transcript_file(transcript_path)
        except Exception as e:
            logger.warning(f"Could not read transcript file for song identification: {e}")

        # Step 4: Search for lyrics
        lyrics_content = search_lyrics_step(
            {
                'title': results.metadata_title,
                'artist': results.metadata_artist,
                'album': results.metadata_album,
                'genre': results.metadata_genre,
                'year': results.metadata_year,
                'track_number': results.metadata_track_number
            },
            paths,
            resume,
            results,
            transcript_content
        )

        # Step 4.5: Apply grammatical correction if lyrics not found
        corrected_transcript_content = None
        if not lyrics_content:
            corrected_transcript_content = grammatical_correction_step(paths, resume, results)

        # Step 5: Generate LRC file
        transcript_path = str(paths['transcript_txt'])
        if not generate_lrc_step(lyrics_content, corrected_transcript_content, transcript_path, paths, resume, results):
            results.finalize()
            return False, results.to_dict()

        # Step 6: Add translation to Traditional Chinese
        lrc_path = str(paths['lrc'])
        if not translate_lrc_step(lrc_path, paths, resume, log_level, results):
            results.finalize()
            return False, results.to_dict()

        results.finalize()
        return results.overall_success, results.to_dict()

    except Exception as e:
        results.error_message = str(e)
        results.overall_success = False
        results.finalize()
        logger.error(f"Error processing file {input_file}: {e}")
        return False, results.to_dict()
            


def main():
    """Main function to process all audio files (FLAC and MP3) in a directory and output results to CSV."""
    parser = argparse.ArgumentParser(
        description='Process all audio files (FLAC and MP3) in a folder (recursive) to create LRC files with translation. Outputs detailed results to CSV.'
    )
    parser.add_argument(
        'input_dir',
        nargs='?',
        default='input',
        help='Input directory containing audio files (FLAC or MP3) (default: input)'
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
        default=f'results_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
        help='CSV file to save processing results (default: processing_results_YYYYMMDD_HHMMSS.csv)'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored logging output (default: False)'
    )
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    use_colors = not args.no_color
    setup_logging(level=log_level, use_colors=use_colors)
    
    logger.info(f"Starting audio file lyric processing for directory: {args.input_dir}")
    
    # Ensure output directory exists
    if not ensure_output_directory(args.output_dir):
        logger.error("Failed to create output directory, exiting...")
        return 1
    
    # Create temporary directory
    Path(args.temp_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temporary directory: {args.temp_dir}")
    
    # Find all audio files (FLAC and MP3)
    audio_files = find_audio_files(args.input_dir)

    if not audio_files:
        logger.warning(f"No audio files (FLAC or MP3) found in {args.input_dir}")
        return 0

    # Process each audio file
    success_count = 0
    all_results = []
    for audio_file in audio_files:
        logger.info(f"Processing {audio_file} ({success_count + 1}/{len(audio_files)})")
        success, results = process_single_audio_file(audio_file, args.output_dir, args.temp_dir, args.resume, log_level, args.input_dir)
        all_results.append(results)

        if success:
            success_count += 1
        else:
            logger.error(f"Failed to process {audio_file}")

    logger.info(f"Processing completed. Successfully processed {success_count}/{len(audio_files)} files.")

    # Write results to CSV
    logger.info(f"Writing processing results to CSV: {args.csv_output}")
    if write_csv_results(args.csv_output, all_results):
        logger.info(f"CSV file saved successfully with {len(all_results)} records")
    else:
        logger.error("Failed to write CSV file")
    
    return 0 if success_count == len(audio_files) else 1


if __name__ == "__main__":
    sys.exit(main())

