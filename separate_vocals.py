#!/usr/bin/env python3
"""
Script to preprocess audio files using audio-separator to extract vocals only.
Transcription functionality has been moved to transcribe_vocals.py.
"""

import os
import logging
from audio_separator.separator import Separator
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def separate_vocals(input_file_path, output_dir="output", model="UVR_MDXNET_Main.onnx", vocals_output_path=None):
    """
    Separate vocals from an audio file using audio-separator.

    Args:
        input_file_path (str): Path to the input audio file
        output_dir (str): Directory to save the separated audio files (default: "output")
        model (str): Model to use for separation (default: "UVR_MDXNET_Main.onnx")
        vocals_output_path (str): Specific path for the vocals output file (optional)

    Returns:
        str: Path to the vocals file if successful, None otherwise
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # If specific vocals output path is provided, create the parent directory
    if vocals_output_path:
        vocals_dir = os.path.dirname(vocals_output_path)
        os.makedirs(vocals_dir, exist_ok=True)
    
    # Create the model directory if it doesn't exist
    model_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    # Initialize the separator with CPU (since we're using the CPU version)
    separator = Separator(log_level=logging.INFO)
    
    # Set the model and output directory
    separator.model_file_dir = model_dir
    separator.output_dir = output_dir
    separator.single_stem = "Vocals" # Only output the vocals stem
    
    # Load the model
    separator.load_model(model_filename=model)
    
    # Load and separate the audio
    logger.info(f"Loading audio file: {input_file_path}")
    output_files = separator.separate(input_file_path)
    
    # Find the vocals file in the output
    vocals_file = None
    for output_file in output_files:
        if "Vocals" in output_file or "vocals" in output_file or "Vocal" in output_file or "vocal" in output_file:
            vocals_file = output_file
            break

    if vocals_file:
        # Get the full path to the vocals file in the output directory
        full_vocals_path = os.path.join(output_dir, os.path.basename(vocals_file))

        # If specific output path is provided, move the file there
        if vocals_output_path:
            try:
                # Move the file from output directory to the desired location
                import shutil
                shutil.move(full_vocals_path, vocals_output_path)
                logger.info(f"Vocals file moved to: {vocals_output_path}")

                # Delete instrumental and other non-vocals files to save space
                _cleanup_non_vocals_files(output_files, output_dir)

                return vocals_output_path
            except Exception as e:
                logger.error(f"Failed to move vocals file to {vocals_output_path}: {e}")
                # Return the original path if move fails
                return full_vocals_path
        else:
            logger.info(f"Vocals extracted successfully: {full_vocals_path}")

            # Delete instrumental and other non-vocals files to save space
            _cleanup_non_vocals_files(output_files, output_dir)

            return full_vocals_path
    else:
        logger.error("Could not find vocals track in the separated files")
        logger.info(f"Available output files: {output_files}")

        # If we can't find a vocals file, return the first file that might contain vocals
        for output_file in output_files:
            if any(stem in output_file.lower() for stem in ["vocal", "voice"]):
                source_path = os.path.join(output_dir, os.path.basename(output_file))
                if vocals_output_path:
                    try:
                        # Move the file to the desired location
                        import shutil
                        shutil.move(source_path, vocals_output_path)
                        logger.info(f"Vocals file moved to: {vocals_output_path}")

                        # Delete instrumental and other non-vocals files to save space
                        _cleanup_non_vocals_files(output_files, output_dir)

                        return vocals_output_path
                    except Exception as e:
                        logger.error(f"Failed to move vocals file to {vocals_output_path}: {e}")
                        return source_path
                else:
                    # Delete instrumental and other non-vocals files to save space
                    _cleanup_non_vocals_files(output_files, output_dir)
                    return source_path

        # If still no vocal file found, return the first available output file
        if output_files:
            logger.info(f"Using first available output file: {output_files[0]}")
            source_path = os.path.join(output_dir, os.path.basename(output_files[0]))
            if vocals_output_path:
                try:
                    # Move the file to the desired location
                    import shutil
                    shutil.move(source_path, vocals_output_path)
                    logger.info(f"Vocals file moved to: {vocals_output_path}")

                    # Delete instrumental and other non-vocals files to save space
                    _cleanup_non_vocals_files(output_files, output_dir)

                    return vocals_output_path
                except Exception as e:
                    logger.error(f"Failed to move vocals file to {vocals_output_path}: {e}")
                    return source_path
            else:
                # Delete instrumental and other non-vocals files to save space
                _cleanup_non_vocals_files(output_files, output_dir)
                return source_path

        return None


def _cleanup_non_vocals_files(output_files, output_dir):
    """
    Delete instrumental and other non-vocals files created by UVR to save disk space.

    Args:
        output_files (list): List of all output files created by audio-separator
        output_dir (str): Directory where the files are located
    """
    if not output_files:
        return

    vocals_patterns = ["vocals", "Vocals", "vocal", "Vocal"]
    instrumental_patterns = ["instrumental", "Instrumental", "drums", "Drums", "bass", "Bass", "other", "Other"]

    vocals_files = []
    instrumental_files = []

    # Categorize files
    for output_file in output_files:
        filename = os.path.basename(output_file)
        full_path = os.path.join(output_dir, filename)

        # Check if this is a vocals file
        is_vocals = any(pattern in filename for pattern in vocals_patterns)

        if is_vocals:
            vocals_files.append(full_path)
        else:
            # Check if it might be instrumental or other non-vocals
            is_instrumental = any(pattern in filename for pattern in instrumental_patterns)
            if is_instrumental or not any(pattern in filename for pattern in vocals_patterns):
                instrumental_files.append(full_path)

    # Delete instrumental files
    for instrumental_file in instrumental_files:
        try:
            if os.path.exists(instrumental_file):
                os.remove(instrumental_file)
                logger.info(f"Deleted instrumental file: {instrumental_file}")
        except Exception as e:
            logger.warning(f"Failed to delete instrumental file {instrumental_file}: {e}")

    if instrumental_files:
        logger.info(f"Cleaned up {len(instrumental_files)} instrumental files, kept {len(vocals_files)} vocals file(s)")



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

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)

    # Define the input file path
    input_file = args.file_path

    # Check if the input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        return

    logger.info(f"Starting vocal separation for: {input_file}")

    # Separate vocals
    vocals_file = separate_vocals(input_file, output_dir=args.output_dir, model=args.model)

    if vocals_file:
        logger.info(f"Successfully extracted vocals to: {vocals_file}")
    else:
        logger.error("Failed to extract vocals")

if __name__ == "__main__":
    main()