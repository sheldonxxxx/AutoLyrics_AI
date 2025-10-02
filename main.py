#!/usr/bin/env python3
"""
Main entry point for the music lyric processing pipeline.
This script coordinates the various components of the music lyric processing system.
"""

import logging
import argparse
import os
import sys
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Music lyric processing pipeline.')
    parser.add_argument('action', nargs='?', default='overview',
                        choices=['overview', 'metadata', 'search', 'separate', 'generate', 'translate'],
                        help='Action to perform (default: overview)')
    parser.add_argument('--file', '-f',
                        help='Input audio file path')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)
    
    logger.info(f"Starting music-lyric processing: {args.action}")
    
    if args.action == 'overview':
        logger.info("Music lyric processing pipeline")
        logger.info("Available actions:")
        logger.info("  metadata  - Extract metadata from audio file")
        logger.info("  search    - Search for lyrics online")
        logger.info("  separate  - Separate vocals and transcribe")
        logger.info(" generate  - Generate LRC lyrics from transcript")
        logger.info("  translate - Translate LRC lyrics to another language")
        logger.info("")
        logger.info("Usage: python main.py [action] [options]")
        logger.info("Example: python main.py search --file my_song.flac")
    
    elif args.action == 'metadata':
        from extract_metadata import extract_metadata
        logger.info(f"Extracting metadata from: {args.file}")
        metadata = extract_metadata(args.file)
        logger.info("Extracted Metadata:")
        for key, value in metadata.items():
            logger.info(f"  {key}: {value}")
    
    elif args.action == 'search':
        from extract_metadata import extract_metadata
        from search_lyrics import search_uta_net
        logger.info(f"Searching for lyrics for: {args.file}")
        
        metadata = extract_metadata(args.file)
        if metadata['title'] and metadata['artist']:
            lyrics = search_uta_net(metadata['title'], metadata['artist'])
            if lyrics:
                logger.info(f"Lyrics found for '{metadata['title']}' by {metadata['artist']}")
                # Save to file
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                output_filename = f"{os.path.splitext(os.path.basename(args.file))[0]}_lyrics.txt"
                output_file = os.path.join(output_dir, output_filename)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Lyrics for '{metadata['title']}' by {metadata['artist']}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(lyrics)
                    f.write(f"\n\nSource: uta-net.com")
                logger.info(f"Lyrics saved to: {output_file}")
            else:
                logger.warning(f"Could not find lyrics for '{metadata['title']}' by {metadata['artist']}")
        else:
            logger.error("Missing title or artist information. Cannot search for lyrics.")
    
    elif args.action == 'separate':
        from separate_vocals import separate_vocals, transcribe_with_timestamps
        logger.info(f"Separating vocals from: {args.file}")
        
        # Separate vocals
        vocals_file = separate_vocals(args.file)
        if vocals_file:
            logger.info(f"Successfully extracted vocals to: {vocals_file}")
            
            # Transcribe the vocals with timestamps
            logger.info("Starting transcription with timestamps...")
            segments = transcribe_with_timestamps(vocals_file)
            
            if segments:
                logger.info(f"Transcription completed with {len(segments)} segments.")
                
                # Save the transcription to a file
                transcript_file = vocals_file.replace('.wav', '_transcript.txt')
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write("Timestamped Transcription:\n\n")
                    for segment in segments:
                        f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
                logger.info(f"Transcription saved to: {transcript_file}")
            else:
                logger.error("Transcription failed.")
        else:
            logger.error("Failed to extract vocals")
    
    elif args.action == 'generate':
        from generate_lrc import read_lyrics_file, read_transcript_file, generate_lrc_lyrics
        from openai import OpenAI
        from dotenv import load_dotenv
        import os
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration from environment variables
        base_url = os.getenv("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1")
        api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not api_key:
            logger.error("Error: OPENAI_API_KEY environment variable not set")
            return
        
        # Initialize the OpenAI client with the custom base URL
        client = OpenAI(base_url=base_url, api_key=api_key)
        
        # Define file paths
        lyrics_file_path = f"output/{os.path.splitext(os.path.basename(args.file))[0]}_lyrics.txt"
        transcript_file_path = f"output/{os.path.splitext(os.path.basename(args.file))[0]}_(Vocals)_UVR_MDXNET_Main_transcript.txt"
        output_lrc_path = f"output/{os.path.splitext(os.path.basename(args.file))[0]}.lrc"
        
        # Check if the input files exist
        if not os.path.exists(lyrics_file_path):
            logger.error(f"Lyrics file does not exist: {lyrics_file_path}")
            return
        
        if not os.path.exists(transcript_file_path):
            logger.error(f"Transcript file does not exist: {transcript_file_path}")
            return
        
        logger.info("Reading lyrics and transcript files...")
        
        # Read the lyrics and transcript
        lyrics_text = read_lyrics_file(lyrics_file_path)
        asr_transcript = read_transcript_file(transcript_file_path)
        
        logger.info("Generating LRC formatted lyrics...")
        
        # Generate the LRC lyrics
        lrc_lyrics = generate_lrc_lyrics(client, lyrics_text, asr_transcript)
        
        if lrc_lyrics:
            logger.info("LRC lyrics generated successfully!")
            
            # Save the LRC lyrics to a file
            with open(output_lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_lyrics)
            
            logger.info(f"LRC lyrics saved to: {output_lrc_path}")
        else:
            logger.error("Failed to generate LRC lyrics.")
    
    elif args.action == 'translate':
        from translate_lrc import main as translate_main
        input_lrc_path = f"output/{os.path.splitext(os.path.basename(args.file))[0]}.lrc"
        output_lrc_path = f"output/{os.path.splitext(os.path.basename(args.file))[0]}_Traditional_Chinese.lrc"
        
        success = translate_main(input_lrc_path, output_lrc_path, "Traditional Chinese", log_level)
        if success:
            logger.info("Translation completed successfully!")
        else:
            logger.error("Translation failed.")


if __name__ == "__main__":
    main()
