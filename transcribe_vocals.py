#!/usr/bin/env python3
"""
Transcribe vocals with timestamped transcription using faster-whisper.

This module handles ASR transcription for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/transcribe_vocals.md

Key Features:
- Multiple Whisper model sizes (tiny to large-v3)
- Word-level timestamp accuracy
- CPU-compatible processing
- Configurable accuracy vs. speed trade-offs

Dependencies:
- faster-whisper>=1.2.0 (optimized Whisper implementation)
- logging_config (pipeline logging)

Model Sizes: tiny, base, small, medium, large-v1/v2/v3, large-v3-turbo

Pipeline Stage: 3/6 (ASR Transcription)
"""

import os
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def transcribe_with_timestamps(audio_file_path, model_size="large-v3", device="cpu", compute_type="int8"):
    """
    Transcribe an audio file with timestamped transcription using faster-whisper.

    Args:
        audio_file_path (str): Path to the audio file to transcribe
        model_size (str): Size of the Whisper model to use (default: "large-v3")
        device (str): Device to run the model on (default: "cpu")
        compute_type (str): Type of computation to use (default: "int8")

    Returns:
        list: List of segments with timestamps and text
    """
    logger = get_logger(__name__)
    try:
        from faster_whisper import WhisperModel

        # Load the model
        model = WhisperModel(model_size, device=device, compute_type=compute_type)


        # Transcribe the audio with word-level timestamps
        segments, _ = model.transcribe(audio_file_path, beam_size=5, word_timestamps=True)

        # # Convert segments to a list to force transcription
        segment_list = list(segments)

        # Print the transcribed segments with timestamps
        for segment in segment_list:
            logger.debug(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        return segment_list

    except ImportError:
        logger.exception("faster-whisper is not installed. Please install it with: pip install faster-whisper")
        return []
    except Exception as e:
        logger.exception(f"Error during transcription: {e}")
        return []

def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Transcribe vocals with timestamped transcription using faster-whisper.')
    parser.add_argument('file_path', nargs='?',
                        help='Path to the input audio file')
    parser.add_argument('--model', default="large-v3",
                        help='Whisper model size to use for transcription (default: large-v3)')
    parser.add_argument('--device', default="cpu",
                        help='Device to run the transcription model on (default: cpu)')
    parser.add_argument('--compute-type', default="int8",
                        help='Type of computation to use for transcription (default: int8)')
    parser.add_argument('--log-level', default='INFO',
                         choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                         help='Logging level (default: INFO)')
    parser.add_argument('--logfire', action='store_true',
                         help='Enable Logfire integration')

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

    logger.info(f"Starting transcription for: {input_file}")

    # Transcribe the vocals with timestamps
    segments = transcribe_with_timestamps(
        input_file,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type
    )

    if segments:
        logger.info(f"\nTranscription completed with {len(segments)} segments.")

        # Optionally, save the transcription to a file
        transcript_file = str(Path(input_file).with_suffix('.txt'))
        transcript_word_file = str(Path(input_file).stem + '_word.txt')
        # Create directory if it doesn't exist
        transcript_dir = os.path.dirname(transcript_file)
        if transcript_dir:
            os.makedirs(transcript_dir, exist_ok=True)

        with open(transcript_file, 'w', encoding='utf-8') as f:
            with open(transcript_word_file, 'w', encoding='utf-8') as word_f:
                for segment in segments:
                    for word in segment.words:
                        word_f.write(f"[{word.start:.2f}s -> {word.end:.2f}s] {word.word}\n")
                    f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
        logger.info(f"Transcription saved to: {transcript_file}")
    else:
        logger.exception("Transcription failed.")

if __name__ == "__main__":
    main()