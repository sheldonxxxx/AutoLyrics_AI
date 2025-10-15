#!/usr/bin/env python3
"""
Process all audio files in a directory through the complete lyrics pipeline.

This module is the flagship component of the Music Lyrics Processing Pipeline,
providing comprehensive batch processing capabilities for entire music libraries.
For comprehensive documentation, see: docs/modules/process_lyrics.md

Key Features:
- Complete six-stage pipeline orchestration
- Recursive file discovery and processing
- Resume functionality for interrupted batches
- Comprehensive CSV reporting and progress tracking

Dependencies:
- All pipeline modules (extract_metadata, separate_vocals, etc.)
- logging_config (centralized logging)
- utils (file operations and validation)

Pipeline Stages: 1-6 (Complete workflow orchestration)

Processing: Sequential per file, parallel across pipeline stages
"""

import os
import sys
import json
from pathlib import Path
import logging
import argparse
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

from logging_config import setup_logging, get_logger
from extract_metadata import extract_metadata
from separate_vocals import separate_vocals
from transcribe_vocals_stable import transcribe_with_timestamps, normalize_audio
from generate_lrc import read_file, generate_lrc_lyrics, correct_grammar_in_transcript
from verify_and_correct_timestamps import verify_and_correct_timestamps
from translate_lrc import translate_lrc_content
from identify_song import identify_song_from_asr
from utils import (
    find_audio_files, ensure_output_directory, get_output_paths,
    parse_transcript_segments, convert_transcript_to_lrc,
    write_csv_results, validate_lrc_content, write_file
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


        self.lrc_generation_success = False
        self.lrc_line_count = 0
        self.lrc_has_timestamps = False

        self.timestamp_verification_success = False
        self.timestamp_corrections_applied = 0
        self.corrected_lrc_path = ''

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
            'lrc_generation_success': self.lrc_generation_success,
            'lrc_line_count': self.lrc_line_count,
            'lrc_has_timestamps': self.lrc_has_timestamps,
            'timestamp_verification_success': self.timestamp_verification_success,
            'timestamp_corrections_applied': self.timestamp_corrections_applied,
            'corrected_lrc_path': self.corrected_lrc_path,
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
        logger.exception(f"Failed to extract metadata for {input_file}: {e}")
        return False


def separate_vocals_step(input_file: Path, paths: dict, resume: bool, results: ProcessingResults) -> bool:
    """Step 2: Separate vocals using UVR."""
    vocals_path = paths['vocals_wav']
    
    logger.info("Step 2: Separating vocals using UVR...")

    if resume and vocals_path.exists():
        logger.info(f"Vocals file already exists for {input_file}, skipping vocal separation...")
        vocals_file = str(vocals_path)
        results.vocals_separation_success = True
        results.vocals_file_path = vocals_file
        results.vocals_file_size = Path(vocals_file).stat().st_size
        return True

    try:
        vocals_file = separate_vocals(str(input_file), paths['vocals_wav'])
        if vocals_file and Path(vocals_file).exists():
            results.vocals_separation_success = True
            results.vocals_file_path = vocals_file
            results.vocals_file_size = Path(vocals_file).stat().st_size
            return True
        else:
            results.vocals_separation_success = False
            results.error_message = "Vocal separation returned no file"
            logger.exception(f"Failed to separate vocals for {input_file}")
            return False

    except Exception as e:
        results.vocals_separation_success = False
        results.error_message = f"Vocal separation failed: {e}"
        logger.exception(f"Exception during vocal separation for {input_file}: {e}")
        return False


def transcribe_vocals_step(vocals_file: str, paths: dict, resume: bool, results: ProcessingResults) -> Optional[List[SimpleNamespace]]:
    """Step 3: Normalize vocals and transcribe with ASR and timestamps."""
    transcript_path = paths['transcript_txt']
    # normalized_vocals_path = paths['normalized_vocals_wav']

    # logger.info("Step 3: Normalizing vocals and transcribing with ASR...")

    if resume and transcript_path.exists():
        logger.info(f"ASR transcript already exists for {vocals_file}, skipping ASR...")
        logger.info("Loading existing ASR transcript...")
        transcript_content = read_file(str(transcript_path))
        return parse_transcript_segments(transcript_content)

    try:
        # Step 3a: Normalize vocals
        logger.info(f"Normalizing vocals: {vocals_file}")
        vocals_path = Path(vocals_file)
        # normalized_path = Path(normalized_vocals_path)

        # if not normalize_audio(vocals_path, normalized_path):
        #     logger.error(f"Failed to normalize vocals: {vocals_file}")
        #     results.transcription_success = False
        #     results.error_message = "Audio normalization failed"
        #     return None

        # Step 3b: Transcribe the normalized vocals
        # logger.info(f"Transcribing normalized vocals: {normalized_path}")
        logger.info(f"Transcribing vocals: {vocals_path}")
        segments = transcribe_with_timestamps(str(vocals_path))
        if segments:
            results.transcription_success = True
            results.transcription_segments_count = len(segments)
            if segments:
                total_duration = max(segment.end for segment in segments)
                results.transcription_duration = total_duration

            # Save transcript to file
            transcript_file = str(paths['transcript_txt'])
            transcript_word_file = str(paths['transcript_word_txt'])
            with open(transcript_file, 'w', encoding='utf-8') as f:
                with open(transcript_word_file, 'w', encoding='utf-8') as word_f:
                    for segment in segments:
                        if hasattr(segment, 'words'):
                            for word in segment.words:
                                word_f.write(f"[{word.start:.2f}s -> {word.end:.2f}s] {word.text}\n")
                        f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
            logger.info(f"Transcription completed: {len(segments)} segments, saved to: {transcript_file}")
            return True
        else:
            results.transcription_success = False
            results.error_message = "Transcription returned no segments"
            logger.exception(f"Failed to transcribe vocals for {vocals_file}")
            return False

    except Exception as e:
        results.transcription_success = False
        results.error_message = f"Transcription failed: {e}"
        logger.exception(f"Exception during transcription for {vocals_file}: {e}")
        return None

def identify_and_search_lyrics_step(metadata: dict, paths: dict, resume: bool, results: ProcessingResults, transcript_content: Optional[str] = None) -> Optional[str]:
    """Step 4: Identify song and search for lyrics using LLM and web search."""

    # Check if we have metadata
    has_metadata = metadata['title'] and metadata['artist']

    # Try to identify song and get lyrics using LLM
    logger.info("Step 4: Identifying song and searching for lyrics using LLM...")

    try:
        # Use different approach based on whether we have metadata
        if has_metadata:
            logger.info(f"Using metadata + ASR approach for '{metadata['title']}' by {metadata['artist']}")
            identified_song = identify_song_from_asr(
                transcript_content,
                paths,
                force_recompute=not resume,
                metadata=metadata
            )
        else:
            logger.info("Using ASR-only approach for song identification")
            identified_song = identify_song_from_asr(
                transcript_content,
                paths,
                force_recompute=not resume,
            )

        if identified_song:
            song_title, artist_name, native_language, lyrics_content, lyrics_source_url = identified_song

            # Update metadata with identified information (if not already set)
            if not has_metadata:
                metadata['title'] = song_title
                metadata['artist'] = artist_name
                results.metadata_title = song_title
                results.metadata_artist = artist_name

            if lyrics_content:
                results.lyrics_search_success = True
                results.lyrics_source = lyrics_source_url or f'LLM search (identified from ASR: {native_language})'
                results.lyrics_length = len(lyrics_content)
                results.lyrics_line_count = len(lyrics_content.split('\n'))

                return lyrics_content
            else:
                logger.warning(f"Song identified but no lyrics found for '{song_title}' by {artist_name}")
                results.lyrics_search_success = False
                results.lyrics_source = f'LLM search (identified from ASR: {native_language}, no lyrics found)'
                return None
        else:
            logger.warning("Could not identify song from ASR transcript")
            results.lyrics_search_success = False
            results.error_message = "Song identification failed"
            return None

    except Exception as e:
        results.lyrics_search_success = False
        results.error_message = f"Song identification and lyrics search failed: {e}"
        logger.exception(f"Exception during song identification and lyrics search: {e}")
        return None

def generate_lrc_step(lyrics_content: Optional[str], corrected_transcript_content: Optional[str], transcript_path: str, paths: dict, resume: bool, results: ProcessingResults) -> bool:
    """Step 5: Generate LRC file by combining lyrics and ASR transcript."""
    lrc_path = paths['lrc']
    
    logger.info("Step 5: Generating LRC file...")

    if resume and lrc_path.exists():
        logger.info(f"LRC file already exists, skipping LRC generation...")
    else:
        # Read transcript file content
        asr_transcript = read_file(transcript_path)

        # Generate LRC
        if lyrics_content:
            lrc_lyrics = generate_lrc_lyrics(lyrics_content, asr_transcript)
        elif corrected_transcript_content:
            logger.info("No lyrics found, using grammatically corrected transcript for LRC generation...")
            lrc_lyrics = generate_lrc_lyrics(corrected_transcript_content, asr_transcript)
        else:
            logger.info("No lyrics found and no corrected transcript, converting ASR transcript to LRC format...")
            lrc_lyrics = convert_transcript_to_lrc(asr_transcript)

        if lrc_lyrics and validate_lrc_content(lrc_lyrics):
            results.lrc_generation_success = True

            # Save LRC file
            write_file(str(lrc_path), lrc_lyrics)
            logger.info(f"LRC generated and saved to: {lrc_path}")
            return True
        else:
            results.lrc_generation_success = False
            results.error_message = "LRC generation returned no content"
            logger.exception("Failed to generate LRC")
            return False

    return True


def verify_and_correct_timestamps_step(lrc_path: str, transcript_path: str, paths: dict, resume: bool, results: ProcessingResults) -> bool:
    """Step 5.5: Verify and correct LRC timestamps using ASR transcript."""
    corrected_lrc_path = paths['corrected_lrc']

    logger.info("Step 5.5: Verifying and correcting LRC timestamps...")

    if resume and corrected_lrc_path.exists():
        logger.info(f"Corrected LRC file already exists, skipping timestamp verification...")
        results.timestamp_verification_success = True
        results.corrected_lrc_path = str(corrected_lrc_path)
        return True

    try:
        # Read the current LRC content
        lrc_content = read_file(lrc_path)
        if not lrc_content:
            results.timestamp_verification_success = False
            results.error_message = "Could not read LRC file for timestamp verification"
            logger.exception("LRC file is empty or could not be read")
            return False

        # Read the ASR transcript content
        asr_transcript = read_file(transcript_path)
        if not asr_transcript:
            results.timestamp_verification_success = False
            results.error_message = "Could not read ASR transcript for timestamp verification"
            logger.exception("ASR transcript file is empty or could not be read")
            return False

        # Verify and correct timestamps
        corrected_lrc_content = verify_and_correct_timestamps(lrc_content, asr_transcript)

        if corrected_lrc_content:
            # Save the corrected LRC content
            write_file(str(corrected_lrc_path), corrected_lrc_content)

            results.timestamp_verification_success = True
            results.corrected_lrc_path = str(corrected_lrc_path)

            # Count corrections by comparing original and corrected content
            original_lines = set(lrc_content.strip().split('\n'))
            corrected_lines = set(corrected_lrc_content.strip().split('\n'))
            corrections_count = len(original_lines.symmetric_difference(corrected_lines))
            results.timestamp_corrections_applied = corrections_count

            logger.info(f"LRC timestamps verified and corrected, saved to: {corrected_lrc_path}")
            logger.info(f"Applied {corrections_count} timestamp corrections")
            return True
        else:
            results.timestamp_verification_success = False
            results.error_message = "Timestamp verification returned no corrected content"
            logger.exception("Failed to verify and correct LRC timestamps")
            return False

    except Exception as e:
        results.timestamp_verification_success = False
        results.error_message = f"Timestamp verification failed: {e}"
        logger.exception(f"Exception during timestamp verification: {e}")
        return False


def translate_lrc_step(lrc_path: str, paths: dict, target_language: str, resume: bool, log_level: int, results: ProcessingResults) -> bool:
    """Step 6: Add translation to Traditional Chinese."""
    translated_lrc_path = paths['translated_lrc']

    logger.info("Step 6: Adding translation to Lyrics...")

    if resume and translated_lrc_path.exists():
        results.overall_success = True
        logger.info(f"Translated LRC file already exists, skipping translation...")
        return True
    
    translated_lrc_content = translate_lrc_content(read_file(str(lrc_path)), target_language)

    if translated_lrc_content:
        logger.info("LRC content translated successfully!")
        logger.debug(f"Translated LRC content length: {len(translated_lrc_content)} characters")
        logger.debug(f"Translated LRC content sample: {translated_lrc_content[:300]}...")  # First 30 chars
        
        # Validate the translated content
        if validate_lrc_content(translated_lrc_content):
            logger.info("Translated LRC content validation passed")
        else:
            logger.warning("Translated LRC content validation failed, but saving anyway")

        # Add metadata tags at the beginning of the final LRC content
        metadata_tags = []
        if results.metadata_title:
            metadata_tags.append(f"[ti:{results.metadata_title}]")
        if results.metadata_artist:
            metadata_tags.append(f"[ar:{results.metadata_artist}]")
        if results.metadata_album:
            metadata_tags.append(f"[al:{results.metadata_album}]")

        # Combine metadata tags with translated LRC content
        if metadata_tags:
            final_lrc_content = "\n".join(metadata_tags) + "\n\n" + translated_lrc_content
        else:
            final_lrc_content = translated_lrc_content

        # Save the final LRC with metadata to file
        write_file(str(translated_lrc_path), final_lrc_content)
            
        results.translation_success = True
        results.overall_success = True
        logger.info(f"Bilingual LRC lyrics saved to: {translated_lrc_path}")
        return True
    else:
        results.translation_success = False
        results.error_message = "Translation failed"
        logger.exception("Translation failed")
        return False

def process_single_audio_file(
    input_file: Path,
    output_dir: str = "output",
    target_language: str = "Traditional Chinese",
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
    
    if paths['translated_lrc'].exists() and resume:
        logger.info(f"Final LRC file already exists for {input_file}, skipping processing...")
        # Read song name and artist from tmp JSON file for CSV reporting
        json_file_path = paths['song_identification']
        if json_file_path.exists():
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)

                # Update results with data from JSON file
                results.metadata_title = json_data.get('song_title', '')
                results.metadata_artist = json_data.get('artist_name', '')
                results.metadata_success = True

                logger.info(f"Loaded song info from JSON: {results.metadata_title} - {results.metadata_artist}")

            except Exception as e:
                logger.warning(f"Failed to read song identification JSON file: {e}")
                # Continue with empty metadata

        results.overall_success = True
        results.finalize()
        return True, results.to_dict()

    try:
        # Step 1: Extract metadata
        if not extract_metadata_step(input_file, results):
            results.finalize()
            return False, results.to_dict()

        # Step 2: Separate vocals using UVR
        # if not separate_vocals_step(input_file, paths, resume, results):
        #     results.finalize()
        #     return False, results.to_dict()

        # Step 3: Transcribe vocals with ASR and timestamps
        if not transcribe_vocals_step(input_file, paths, resume, results):
            results.finalize()
            return False, results.to_dict()

        # Read transcript content for potential song identification
        transcript_path = str(paths['transcript_txt'])
        transcript_content = None
        try:
            transcript_content = read_file(transcript_path)
        except Exception as e:
            logger.warning(f"Could not read transcript file for song identification: {e}", exc_info=True)
            
        # Step 4: Identify song and search for lyrics using LLM
        lyrics_content = identify_and_search_lyrics_step(
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
        
        # If no lyrics found, will skip for now
        # TODO: Consider using grammatically corrected transcript if no lyrics found
        if not lyrics_content:
            results.finalize()
            return False, results.to_dict()

        # Step 5: Generate LRC file
        transcript_path = str(paths['transcript_word_txt'])
        if not generate_lrc_step(lyrics_content, None, transcript_path, paths, resume, results):
            results.finalize()
            return False, results.to_dict()

        # Step 5.5: Verify and correct LRC timestamps
        lrc_path = str(paths['lrc'])
        transcript_path = str(paths['transcript_word_txt'])
        if not verify_and_correct_timestamps_step(lrc_path, transcript_path, paths, resume, results):
            results.finalize()
            return False, results.to_dict()

        # Step 6: Add translation to Traditional Chinese
        corrected_lrc_path = str(paths['corrected_lrc'])
        if not translate_lrc_step(corrected_lrc_path, paths, target_language, resume, log_level, results):
            results.finalize()
            return False, results.to_dict()

        results.finalize()
        return results.overall_success, results.to_dict()

    except Exception as e:
        results.error_message = str(e)
        results.overall_success = False
        results.finalize()
        logger.exception(f"Error processing file {input_file}: {e}")
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
        '--logfire',
        action='store_true',
        help='Enable Logfire integration'
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
    parser.add_argument(
        '--language',
        default='Traditional Chinese',
        help='Target language for translation (default: Traditional Chinese)'
    )
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    use_colors = not args.no_color
    setup_logging(level=log_level, use_colors=use_colors, enable_logfire=args.logfire)
    
    logger.info(f"Starting audio file lyric processing for directory: {args.input_dir}")
    
    # Ensure output directory exists
    if not ensure_output_directory(args.output_dir):
        logger.exception("Failed to create output directory, exiting...")
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
        success, results = process_single_audio_file(audio_file, args.output_dir, args.language ,args.temp_dir, args.resume, log_level, args.input_dir)
        all_results.append(results)

        if success:
            success_count += 1
        else:
            logger.exception(f"Failed to process {audio_file}")

    logger.info(f"Processing completed. Successfully processed {success_count}/{len(audio_files)} files.")

    # Write results to CSV
    logger.info(f"Writing processing results to CSV: {args.csv_output}")
    if write_csv_results(args.csv_output, all_results):
        logger.info(f"CSV file saved successfully with {len(all_results)} records")
    else:
        logger.exception("Failed to write CSV file")
    
    return 0 if success_count == len(audio_files) else 1


if __name__ == "__main__":
    sys.exit(main())

