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

import argparse
import json
from pathlib import Path
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import concurrent
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from dotenv import load_dotenv
from logging_config import setup_logging, get_logger
from extract_metadata import extract_metadata
from transcribe_vocals_stable import transcribe_with_timestamps
from generate_lrc import read_file, generate_lrc_lyrics
from verify_and_correct_timestamps import verify_and_correct_timestamps
from translate_lrc import translate_lrc_content
from identify_song import identify_song_from_asr
from search_song_story import search_song_story
from explain_lyrics import explain_lyrics_content
from utils import (
    get_base_argparser,
    find_audio_files,
    get_output_paths,
    write_csv_results,
    write_file,
    get_default_target_language,
    ProcessingResults,
)

logger = get_logger(__name__)

# Constants
MAX_WORKERS = 10


def process_first_phase(
    input_file: Path,
    paths: dict,
    resume: bool = True,
) -> Tuple[bool, ProcessingResults, dict]:
    """
    First phase processing: metadata extraction, vocal separation, and transcription.

    Args:
        input_file (Path): Input audio file path
        paths (dict): Output file paths dictionary
        resume (bool): Whether to resume processing by skipping existing files

    Returns:
        Tuple[bool, ProcessingResults, dict]: (success, results, paths)
    """
    start_time = time.time()
    results = ProcessingResults.create(input_file, start_time)

    logger.info(f"First phase processing for file: {input_file}")

    try:
        # Step 1: Extract metadata
        if not extract_metadata_step(input_file, results):
            results.finalize()
            return False, results, paths

        # Step 2: Transcribe vocals with ASR and timestamps
        segments = transcribe_vocals_step(str(input_file), paths, resume, results)
        if not segments:
            results.finalize()
            return False, results, paths

        results.finalize()
        logger.info(f"First phase completed for {input_file}")
        return True, results, paths

    except Exception as e:
        results.error_message = str(e)
        results.finalize()
        logger.exception(f"Error in first phase processing for {input_file}")
        return False, results, paths


def process_second_phase(
    input_file: Path,
    paths: dict,
    results: ProcessingResults,
    target_language: str = None,
    resume: bool = True,
) -> Tuple[bool, ProcessingResults]:
    """
    Second phase processing: LLM operations (song identification, LRC generation, translation).

    Args:
        input_file (Path): Input audio file path
        paths (dict): Output file paths dictionary
        results (ProcessingResults): Results object from first phase
        target_language (str): Target language for translation (defaults to env var or English)
        resume (bool): Whether to resume processing by skipping existing files

    Returns:
        Tuple[bool, ProcessingResults]: (success, results)
    """
    if target_language is None:
        target_language = get_default_target_language()
    logger.info(f"Second phase processing for file: {input_file}")

    # Step 4: Identify song and search for lyrics using LLM
    if not identify_and_search_lyrics_step(paths, results, resume):
        results.finalize()
        return False, results

    # Step 5: Generate LRC file
    if not generate_lrc_step(paths, results, resume):
        results.finalize()
        return False, results

    # Step 5.5: Verify and correct LRC timestamps
    if not verify_and_correct_timestamps_step(paths, results, resume):
        results.finalize()
        return False, results

    # Step 6: Search for song story
    if not search_for_song_story_step(paths, results, resume):
        results.finalize()
        return False, results

    # Step 7: Explain lyrics in target language
    if not explain_lyrics_step(paths, target_language, results, resume):
        results.finalize()
        return False, results

    # Step 8: Add translation to Traditional Chinese
    if not translate_lrc_step(paths, target_language, results, resume):
        results.finalize()
        return False, results

    results.finalize()
    logger.info(f"Second phase completed for {input_file}")
    return True, results


def extract_metadata_step(input_file: Path, results: ProcessingResults) -> bool:
    """Step 1: Extract metadata from audio file."""
    logger.info("Step 1: Extracting metadata...")

    try:
        metadata = extract_metadata(str(input_file))
        results.metadata_success = True
        results.metadata_title = metadata.get("title", "")
        results.metadata_artist = metadata.get("artist", "")
        results.metadata_album = metadata.get("album", "")
        results.metadata_genre = metadata.get("genre", "")
        results.metadata_year = str(metadata.get("year", ""))
        results.metadata_track_number = str(metadata.get("track_number", ""))
        logger.info(
            f"Metadata extracted: Title: {metadata.get('title', 'Unknown')} Artist: {metadata.get('artist', 'Unknown')}"
        )

        if not (metadata["title"] and metadata["artist"]):
            logger.warning(f"Missing title or artist for {input_file}")
        return True

    except Exception as e:
        results.metadata_success = False
        results.error_message = f"Metadata extraction failed: {e}"
        logger.exception(f"Exception during metadata extraction for {input_file}")
        return False


def transcribe_vocals_step(
    vocals_file: Path, paths: dict, resume: bool, results: ProcessingResults
) -> bool:
    """Transcribe vocals with ASR and timestamps."""
    transcript_path = paths["transcript_txt"]

    if resume and transcript_path.exists():
        logger.info(f"ASR transcript already exists for {vocals_file}, skipping ASR...")
        return True

    try:
        logger.info(f"Transcribing audio: {vocals_file}")
        transcribe_success = transcribe_with_timestamps(vocals_file, paths)
        if transcribe_success:
            results.transcription_success = True
            return True
        else:
            results.transcription_success = False
            results.error_message = "Transcription failed"
            logger.error(f"Failed to transcribe vocals for {vocals_file}")
            return False

    except Exception as e:
        results.transcription_success = False
        results.error_message = f"Transcription failed: {e}"
        logger.exception(f"Exception during transcription for {vocals_file}")
        return False


def identify_and_search_lyrics_step(
    paths: dict, results: ProcessingResults, resume: bool
) -> bool:
    """Step 4: Identify song and search for lyrics using LLM and web search."""

    # Check if we have metadata
    has_metadata = results.metadata_title and results.metadata_artist

    # Try to identify song and get lyrics using LLM
    logger.info("Step 4: Identifying song and searching for lyrics using LLM...")

    transcript_content = read_file(paths["transcript_txt"])

    # Use different approach based on whether we have metadata
    if has_metadata:
        logger.info("Using metadata + ASR approach for song identification")
        metadata = {
            "title": results.metadata_title,
            "artist": results.metadata_artist,
            "album": results.metadata_album,
        }
        identified_song_success = identify_song_from_asr(
            transcript_content, paths, metadata=metadata, recompute=not resume
        )
    else:
        logger.info("Using ASR-only approach for song identification")
        identified_song_success = identify_song_from_asr(
            transcript_content,
            paths,
            recompute=not resume,
        )

    if identified_song_success:
        result = json.load(open(paths["song_identification"], "r", encoding="utf-8"))

        # Update metadata with identified information (if not already set)
        if not has_metadata:
            results.metadata_title = result["song_title"]
            results.metadata_artist = result["artist_name"]

        results.song_language = result["native_language"]

        if result.get("lyrics_content"):
            results.lyrics_search_success = True
            return True
        else:
            logger.warning(
                f"Song identified but no lyrics found for '{result['song_title']}' by {result['artist_name']}"
            )
            results.lyrics_search_success = False
            return False
    else:
        logger.warning("Could not identify song from ASR transcript")
        results.lyrics_search_success = False
        results.error_message = "Song identification failed"
        return False


def generate_lrc_step(paths: dict, results: ProcessingResults, resume: bool) -> bool:
    """Step 5: Generate LRC file by combining lyrics and ASR transcript."""

    logger.info("Step 5: Generating LRC file...")

    asr_transcript = read_file(paths["transcript_txt"])
    lyrics_test = read_file(paths["lyrics_txt"])

    lrc_lyrics_success = generate_lrc_lyrics(
        asr_transcript, lyrics_test, paths, recompute=not resume
    )

    if lrc_lyrics_success:
        results.lrc_generation_success = True
        return True
    else:
        results.lrc_generation_success = False
        results.error_message = "LRC generation failed"
        logger.exception("Failed to generate LRC")
        return False


def verify_and_correct_timestamps_step(
    paths: dict,
    results: ProcessingResults,
    resume: bool,
) -> bool:
    """Step 5.5: Verify and correct LRC timestamps using ASR transcript."""

    logger.info("Step 5.5: Verifying and correcting LRC timestamps...")

    # Read the current LRC content
    lrc_content = read_file(paths["lrc"])

    # Read the ASR transcript content
    asr_transcript = read_file(paths["transcript_txt"])

    output_lrc_path = paths["corrected_lrc"]

    # Verify and correct timestamps
    correct_lrc_success = verify_and_correct_timestamps(
        lrc_content, asr_transcript, paths, recompute=not resume
    )

    if correct_lrc_success:
        # Add metadata tags at the beginning of the LRC content
        metadata_tags = []
        if results.metadata_title:
            metadata_tags.append(f"[ti:{results.metadata_title}]")
        if results.metadata_artist:
            metadata_tags.append(f"[ar:{results.metadata_artist}]")
        if results.metadata_album:
            metadata_tags.append(f"[al:{results.metadata_album}]")

        # Combine metadata tags with translated LRC content
        if metadata_tags:
            translated_lrc_content = read_file(output_lrc_path)
            final_lrc_content = (
                "\n".join(metadata_tags) + "\n\n" + translated_lrc_content
            )
            write_file(output_lrc_path, final_lrc_content)

        results.timestamp_verification_success = True
        return True
    else:
        results.timestamp_verification_success = False
        results.error_message = "Timestamp verification returned no corrected content"
        logger.exception("Failed to verify and correct LRC timestamps")
        return False


def search_for_song_story_step(
    paths: dict,
    results: ProcessingResults,
    resume: bool,
) -> bool:
    """Step 6: Search for song story using web search."""
    logger.info("Step 6: Searching for song story using web search...")

    song_story_success = search_song_story(
        results.metadata_title,
        results.metadata_artist,
        results.song_language,
        paths,
        recompute=not resume,
    )

    if song_story_success:
        results.song_story_search_success = True
        return True
    else:
        results.song_story_search_success = False
        results.error_message = "Song story search failed"
        logger.error("Failed to search for song story")
        return False


def explain_lyrics_step(
    paths: dict,
    target_language: str,
    results: ProcessingResults,
    resume: bool,
) -> bool:
    """Step 7: Explain lyrics in target language."""

    logger.info("Step 6: Explaining lyrics in target language...")

    song_story = json.load(open(paths["song_story"], "r", encoding="utf-8"))

    # Explain the lyrics content
    explanation_content = explain_lyrics_content(
        read_file(paths["lrc"]),
        paths,
        target_language,
        song_story=song_story,
        recompute=not resume,
    )

    if explanation_content:
        results.explanation_success = True
        return True
    else:
        results.explanation_success = False
        results.error_message = "Lyrics explanation returned no content"
        logger.error("Failed to explain lyrics")
        return False


def translate_lrc_step(
    paths: dict,
    target_language: str,
    results: ProcessingResults,
    resume: bool,
) -> bool:
    """Step 8: Add translation to Traditional Chinese."""
    logger.info("Step 7: Adding translation to Lyrics...")

    lrc_content = read_file(paths["corrected_lrc"])

    song_explanation = read_file(paths["explanation_txt"])

    translate_success = translate_lrc_content(
        lrc_content,
        paths,
        target_language,
        song_explanation=song_explanation,
        recompute=not resume,
    )

    if translate_success:
        results.translation_success = True
        return True
    else:
        results.translation_success = False
        results.error_message = "Translation failed"
        logger.error("Translation failed")
        return False


def setup_arguments() -> "argparse.Namespace":
    """Set up and parse command-line arguments."""
    load_dotenv()

    parser = get_base_argparser(
        description="Process audio files to create LRC files with translation and output results to CSV."
    )

    parser.add_argument(
        "input_dir",
        nargs="?",
        default="input",
        help="Input directory containing audio files (default: input)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory for final LRC files (default: output)",
    )
    parser.add_argument(
        "--temp-dir",
        "-t",
        default="tmp",
        help="Temporary directory for intermediate files (default: tmp)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume processing by skipping files that already have output files (default: False)",
    )
    parser.add_argument(
        "--csv-output",
        "-c",
        default=f'results_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
        help="CSV file to save processing results (default: processing_results_YYYYMMDD_HHMMSS.csv)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored logging output (default: False)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Target language for translation (default: from env or English)",
    )

    args = parser.parse_args()

    if args.language is None:
        args.language = get_default_target_language()

    return args


def setup_logging_and_directories(args: "argparse.Namespace") -> None:
    """Set up logging and create necessary directories."""
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(
        level=log_level, use_colors=not args.no_color, enable_logfire=args.logfire
    )

    logger.info(f"Starting audio file lyric processing for directory: {args.input_dir}")

    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {args.output_dir}")

    # Create temporary directory
    Path(args.temp_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temporary directory: {args.temp_dir}")


def process_phase1(
    audio_files: List[Path], args: "argparse.Namespace"
) -> List[Tuple[Path, bool, ProcessingResults, dict]]:
    """Process Phase 1: Metadata extraction and transcription for all files."""
    logger.info(
        "Starting Phase 1: Metadata extraction and transcription for all files..."
    )
    first_phase_results = []

    # Determine if using progress bar
    log_level = getattr(logging, args.log_level.upper())
    use_progress_bar = log_level >= logging.WARNING

    if use_progress_bar:
        phase1_iterator = tqdm(
            enumerate(audio_files, 1),
            total=len(audio_files),
            desc="Phase 1: Metadata & Transcription",
            unit="files",
        )
    else:
        phase1_iterator = enumerate(audio_files, 1)

    for i, audio_file in phase1_iterator:
        logger.info(f"Phase 1 - Processing {audio_file} ({i}/{len(audio_files)})")

        paths = get_output_paths(
            audio_file, args.output_dir, args.temp_dir, args.input_dir
        )

        success, results, paths = process_first_phase(audio_file, paths, args.resume)
        first_phase_results.append((audio_file, success, results, paths))

        if not success:
            if use_progress_bar:
                phase1_iterator.set_postfix_str(f"Failed: {audio_file.name}")
            else:
                logger.warning(
                    f"Phase 1 failed for {audio_file}: {results.error_message}"
                )

    if use_progress_bar:
        phase1_iterator.close()

    successful_count = len(
        [success for _, success, _, _ in first_phase_results if success]
    )
    logger.info(
        f"Phase 1 completed. {successful_count}/{len(audio_files)} files processed successfully."
    )

    return first_phase_results


def _submit_second_phase_tasks(
    first_phase_results: List[Tuple[Path, bool, ProcessingResults, dict]],
    args: "argparse.Namespace",
) -> Tuple[List[Tuple[Path, "concurrent.futures.Future"]], List[ProcessingResults]]:
    """Submit second phase tasks to thread pool and collect skipped results."""
    second_phase_futures = []
    skipped_results = []

    with ThreadPoolExecutor(
        max_workers=min(MAX_WORKERS, len(first_phase_results))
    ) as executor:
        for (
            audio_file,
            first_phase_success,
            first_phase_results_obj,
            paths,
        ) in first_phase_results:
            if first_phase_success:
                future = executor.submit(
                    process_second_phase,
                    audio_file,
                    paths,
                    first_phase_results_obj,
                    args.language,
                    args.resume,
                )
                second_phase_futures.append((audio_file, future))
            else:
                logger.info(f"Skipping Phase 2 for {audio_file} due to Phase 1 failure")
                skipped_results.append(first_phase_results_obj)

    return second_phase_futures, skipped_results


def _setup_progress_bar(log_level: int, total: int) -> Optional[tqdm]:
    """Set up progress bar if appropriate based on log level."""
    if log_level >= logging.WARNING:
        return tqdm(
            total=total,
            desc="Phase 2: LLM Operations",
            unit="files",
        )
    return None


def _process_future_result(
    audio_file: Path,
    future: "concurrent.futures.Future",
    phase1_results_dict: Dict[Path, ProcessingResults],
    progress_bar: Optional[tqdm],
    use_progress_bar: bool,
) -> ProcessingResults:
    """Process the result of a single future, handling success, failure, and exceptions."""
    try:
        success, results = future.result()
        if success:
            results.overall_success = True
            if not use_progress_bar:
                logger.info(f"Phase 2 completed successfully for {audio_file}")
        else:
            _log_or_set_postfix(
                progress_bar,
                use_progress_bar,
                f"Failed: {audio_file.name}",
                f"Phase 2 failed for {audio_file}: {results.error_message}",
                is_exception=False,
            )
        return results

    except Exception as e:
        _log_or_set_postfix(
            progress_bar,
            use_progress_bar,
            f"Exception: {audio_file.name}",
            f"Exception in Phase 2 for {audio_file}: {e}",
            is_exception=True,
        )
        # Fallback to first phase results on exception
        results_obj = phase1_results_dict.get(audio_file)
        return results_obj if results_obj else ProcessingResults.create(audio_file, 0.0)


def _log_or_set_postfix(
    progress_bar: Optional[tqdm],
    use_progress_bar: bool,
    postfix: str,
    log_message: str,
    is_exception: bool = False,
):
    """Log message or set progress bar postfix based on configuration."""
    if use_progress_bar and progress_bar:
        progress_bar.set_postfix_str(postfix)
    else:
        if is_exception:
            logger.exception(log_message)
        else:
            logger.warning(log_message)


def process_phase2(
    first_phase_results: List[Tuple[Path, bool, ProcessingResults, dict]],
    args: "argparse.Namespace",
) -> List[ProcessingResults]:
    """Process Phase 2: LLM operations for all files using thread pool."""
    logger.info("Starting Phase 2: LLM operations for all files using thread pool...")
    all_results = []
    phase1_results_dict = {
        audio_file: results_obj for audio_file, _, results_obj, _ in first_phase_results
    }

    # Submit tasks and get futures and skipped results
    second_phase_futures, skipped_results = _submit_second_phase_tasks(
        first_phase_results, args
    )
    all_results.extend(skipped_results)

    # Set up progress bar
    log_level = getattr(logging, args.log_level.upper())
    progress_bar = _setup_progress_bar(log_level, len(second_phase_futures))

    # Collect results as they complete
    for audio_file, future in second_phase_futures:
        result = _process_future_result(
            audio_file,
            future,
            phase1_results_dict,
            progress_bar,
            log_level >= logging.WARNING,
        )
        all_results.append(result)
        if progress_bar:
            progress_bar.update(1)

    if progress_bar:
        progress_bar.close()

    logger.info("Phase 2 completed. All files processed.")
    return all_results


def collect_and_write_results(
    all_results: List[ProcessingResults], args: "argparse.Namespace"
) -> int:
    """Collect results, write to CSV, and calculate success count."""
    # Calculate success count for return code
    success_count = len([r for r in all_results if r.overall_success])

    # Write results to CSV
    logger.info(f"Writing processing results to CSV: {args.csv_output}")
    if write_csv_results(args.csv_output, all_results):
        logger.info(f"CSV file saved successfully with {len(all_results)} records")
    else:
        logger.exception("Failed to write CSV file")

    return success_count


def main() -> int:
    """Main function to process all audio files and output results to CSV."""
    args = setup_arguments()

    setup_logging_and_directories(args)

    audio_files = find_audio_files(args.input_dir)

    if not audio_files:
        logger.warning(f"No audio files found in {args.input_dir}")
        return 1

    first_phase_results = process_phase1(audio_files, args)

    all_results = process_phase2(first_phase_results, args)

    collect_and_write_results(all_results, args)


if __name__ == "__main__":
    main()
