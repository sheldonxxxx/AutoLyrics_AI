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

def process_single_flac_file(
    input_file: Path,
    output_dir: str = "output",
    temp_dir: str = "tmp",
    skip_existing: bool = True,
    log_level: int = logging.INFO
) -> bool:
    """
    Process a single FLAC file through the entire workflow.
    
    Args:
        input_file (Path): Input FLAC file path
        output_dir (str): Output directory for final LRC files
        temp_dir (str): Temporary directory for intermediate files
        skip_existing (bool): Whether to skip files that already have output
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger.info(f"Processing file: {input_file}")
    
    # Get output file paths
    paths = get_output_paths(input_file, output_dir, temp_dir)
    
    # Create temp directory if it doesn't exist
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    
    # Check if all outputs already exist and skip if requested
    if skip_existing and all(path.exists() for path in paths.values()):
        logger.info(f"All output files already exist for {input_file}, skipping...")
        return True

    try:
        # Step 1: Extract metadata
        logger.info("Step 1: Extracting metadata...")
        metadata = extract_metadata(str(input_file))
        
        if not (metadata['title'] and metadata['artist']):
            logger.warning(f"Missing title or artist for {input_file}, cannot search for lyrics")
            # We can still continue with vocal separation and ASR even without lyrics

        # Step 2: Separate vocals using UVR (skip if vocals file already exists)
        vocals_path = paths['vocals_wav']
        if skip_existing and vocals_path.exists():
            logger.info(f"Vocals file already exists for {input_file}, skipping vocal separation...")
            vocals_file = str(vocals_path)
        else:
            logger.info("Step 2: Separating vocals using UVR...")
            vocals_file = separate_vocals(str(input_file), output_dir=temp_dir)
            if not vocals_file:
                logger.error(f"Failed to separate vocals for {input_file}")
                return False

        # Step 3: Transcribe vocals with ASR and timestamps (skip if transcript already exists)
        transcript_path = paths['transcript_txt']
        if skip_existing and transcript_path.exists():
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
            segments = transcribe_with_timestamps(vocals_file)
            if not segments:
                logger.error(f"Failed to transcribe vocals for {input_file}")
                return False
            
            # Save transcript to file
            transcript_file = str(paths['transcript_txt'])
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write("Timestamped Transcription:\n\n")
                for segment in segments:
                    f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
            logger.info(f"Transcription saved to: {transcript_file}")

        # Step 4: Search for lyrics (only if we have title and artist, and lyrics file doesn't exist yet)
        lyrics_content = None
        lyrics_path = paths['lyrics_txt']
        if metadata['title'] and metadata['artist']:
            if skip_existing and lyrics_path.exists():
                logger.info(f"Lyrics file already exists for {input_file}, skipping lyrics search...")
                # Read existing lyrics
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
            else:
                logger.info("Step 4: Searching for lyrics...")
                lyrics_content = search_uta_net(metadata['title'], metadata['artist'])
                if lyrics_content:
                    # Save lyrics to file
                    lyrics_file = str(paths['lyrics_txt'])
                    with open(lyrics_file, 'w', encoding='utf-8') as f:
                        f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
                        f.write("=" * 60 + "\n\n")
                        f.write(lyrics_content)
                        f.write(f"\n\nSource: uta-net.com")
                    logger.info(f"Lyrics saved to: {lyrics_file}")
                else:
                    logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
        else:
            logger.info("Skipping lyrics search due to missing title or artist metadata")

        # Step 5: Generate LRC file by combining lyrics and ASR transcript (skip if LRC already exists)
        lrc_path = paths['lrc']
        if skip_existing and lrc_path.exists():
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
                # Save LRC file
                lrc_file = str(paths['lrc'])
                with open(lrc_file, 'w', encoding='utf-8') as f:
                    f.write(lrc_lyrics)
                logger.info(f"LRC file saved to: {lrc_file}")
            else:
                logger.error(f"Failed to generate LRC for {input_file}")
                return False

        # Step 6: Add translation to Traditional Chinese (skip if translated LRC already exists)
        translated_lrc_path = paths['translated_lrc']
        if skip_existing and translated_lrc_path.exists():
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
            logger.info(f"Processing completed successfully for {input_file}")
            return True
        else:
            logger.error(f"Translation failed for {input_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {e}")
        return False
    
    try:
        # Step 1: Extract metadata
        logger.info("Step 1: Extracting metadata...")
        metadata = extract_metadata(str(input_file))
        
        if not (metadata['title'] and metadata['artist']):
            logger.warning(f"Missing title or artist for {input_file}, cannot search for lyrics")
            # We can still continue with vocal separation and ASR even without lyrics
        
        # Step 2: Separate vocals using UVR
        logger.info("Step 2: Separating vocals using UVR...")
        vocals_file = separate_vocals(str(input_file), output_dir=temp_dir)
        if not vocals_file:
            logger.error(f"Failed to separate vocals for {input_file}")
            return False
        
        # Step 3: Transcribe vocals with ASR and timestamps
        logger.info("Step 3: Transcribing vocals with ASR...")
        segments = transcribe_with_timestamps(vocals_file)
        if not segments:
            logger.error(f"Failed to transcribe vocals for {input_file}")
            return False
        
        # Save transcript to file
        transcript_file = str(paths['transcript_txt'])
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write("Timestamped Transcription:\n\n")
            for segment in segments:
                f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
        logger.info(f"Transcription saved to: {transcript_file}")
        
        # Step 4: Search for lyrics (only if we have title and artist)
        lyrics_content = None
        if metadata['title'] and metadata['artist']:
            logger.info("Step 4: Searching for lyrics...")
            lyrics_content = search_uta_net(metadata['title'], metadata['artist'])
            if lyrics_content:
                # Save lyrics to file
                lyrics_file = str(paths['lyrics_txt'])
                with open(lyrics_file, 'w', encoding='utf-8') as f:
                    f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(lyrics_content)
                    f.write(f"\n\nSource: uta-net.com")
                logger.info(f"Lyrics saved to: {lyrics_file}")
            else:
                logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
        else:
            logger.info("Skipping lyrics search due to missing title or artist metadata")
        
        # Step 5: Generate LRC file by combining lyrics and ASR transcript
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
        asr_transcript = read_transcript_file(transcript_file)
        
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
            # Save LRC file
            lrc_file = str(paths['lrc'])
            with open(lrc_file, 'w', encoding='utf-8') as f:
                f.write(lrc_lyrics)
            logger.info(f"LRC file saved to: {lrc_file}")
        else:
            logger.error(f"Failed to generate LRC for {input_file}")
            return False
        
        # Step 6: Add translation to Traditional Chinese
        logger.info("Step 6: Adding translation to Traditional Chinese...")
        success = translate_main(
            lrc_file,
            str(paths['translated_lrc']),
            "Traditional Chinese",
            log_level
        )
        
        if success:
            logger.info(f"Processing completed successfully for {input_file}")
            return True
        else:
            logger.error(f"Translation failed for {input_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {e}")
        return False


def main():
    """Main function to process all FLAC files in a directory."""
    parser = argparse.ArgumentParser(
        description='Process all FLAC files in a folder (recursive) to create LRC files with translation.'
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
        '--skip-existing',
        action='store_true',
        help='Skip files that already have output files (default: False)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
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
    for flac_file in flac_files:
        logger.info(f"Processing {flac_file} ({success_count + 1}/{len(flac_files)})")
        if process_single_flac_file(flac_file, args.output_dir, args.temp_dir, args.skip_existing, log_level):
            success_count += 1
        else:
            logger.error(f"Failed to process {flac_file}")
    
    logger.info(f"Processing completed. Successfully processed {success_count}/{len(flac_files)} files.")
    
    return 0 if success_count == len(flac_files) else 1


if __name__ == "__main__":
    sys.exit(main())

