#!/usr/bin/env python3
"""
Separate vocals from audio files using AI-powered source separation.

This module handles vocal separation for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/separate_vocals.md

Key Features:
- AI-powered vocal isolation using UVR models
- Multi-format audio support (FLAC, MP3, WAV, M4A)
- CPU-compatible processing

Dependencies:
- audio-separator[cpu]>=0.39.0 (AI-powered separation)
- logging_config (pipeline logging)

Model: UVR-MDX-NET-Main (optimized for vocal separation)

Pipeline Stage: 2/6 (Vocal Separation)
"""

import os
import logging
from pathlib import Path
from audio_separator.separator import Separator
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def separate_vocals(input_file_path: str, vocals_output_path: Path, model: str ="UVR_MDXNET_Main.onnx"):
    """
    Separate vocals from an audio file using audio-separator.

    Args:
        input_file_path (str): Path to the input audio file
        vocals_output_path (str): Specific path for the vocals output file 
        model (str): Model to use for separation (default: "UVR_MDXNET_Main.onnx")

    Returns:
        str: Path to the vocals file if successful, None otherwise
    """
    
    # Set up output directory
    vocals_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the model directory if it doesn't exist
    model_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    # Initialize the separator with CPU (since we're using the CPU version)
    separator = Separator(log_level=logging.WARNING,
                          model_file_dir=model_dir,
                          output_dir=vocals_output_path.parent,
                          output_single_stem="Vocals")  # Only output the vocals stem
    
    # Load the model
    output_files = separator.load_model(model_filename=model)
    
    # Load and separate the audio
    logger.info(f"Loading audio file: {input_file_path}")
    output_names = {
        "Vocals": vocals_output_path.stem
    }
    separator.separate(input_file_path, output_names)

    if vocals_output_path.exists():
        logger.info(f"Vocals extracted successfully: {vocals_output_path}")
        return str(vocals_output_path)
    else:
        logger.exception("Could not find vocals track in the separated files")
        logger.info(f"Available output files: {output_files}")
        return None

def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Extract vocals from audio files using audio-separator (UVR).')
    parser.add_argument('file_path', nargs='?',
                        help='Path to the input audio file')
    parser.add_argument('--output-dir', '-o', default="output",
                        help='Directory to save the separated audio files (default: output)')
    parser.add_argument('--model', '-m', default="UVR_MDXNET_Main.onnx",
                        help='Model to use for separation (default: UVR_MDXNET_Main.onnx)')
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

    logger.info(f"Starting vocal separation for: {input_file}")

    # Separate vocals
    output_file = Path(args.output_dir) / (Path(input_file).stem + "_vocal.wav")
    vocals_file = separate_vocals(input_file, output_file, model=args.model)

    if vocals_file:
        logger.info(f"Successfully extracted vocals to: {vocals_file}")
    else:
        logger.exception("Failed to extract vocals")

if __name__ == "__main__":
    main()