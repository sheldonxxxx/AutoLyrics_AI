#!/usr/bin/env python3
"""
Script to preprocess audio files using audio-separator to extract vocals only
and transcribe the vocals with timestamped transcription using faster-whisper.
"""

import os
import logging
from audio_separator.separator import Separator
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def separate_vocals(input_file_path, output_dir="output", model="UVR_MDXNET_Main.onnx"):
    """
    Separate vocals from an audio file using audio-separator.
    
    Args:
        input_file_path (str): Path to the input audio file
        output_dir (str): Directory to save the separated audio files (default: "output")
        model (str): Model to use for separation (default: "UVR_MDXNET_Main.onnx")
    
    Returns:
        str: Path to the vocals file if successful, None otherwise
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
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
        # Make sure we return the full path to the vocals file
        full_vocals_path = os.path.join(output_dir, os.path.basename(vocals_file))
        logger.info(f"Vocals extracted successfully: {full_vocals_path}")
        return full_vocals_path
    else:
        logger.error("Could not find vocals track in the separated files")
        logger.info(f"Available output files: {output_files}")
        
        # If we can't find a vocals file, return the first file that might contain vocals
        for output_file in output_files:
            if any(stem in output_file.lower() for stem in ["vocal", "voice"]):
                return os.path.join(output_dir, os.path.basename(output_file))
        
        # If still no vocal file found, return the first available output file
        if output_files:
            logger.info(f"Using first available output file: {output_files[0]}")
            return os.path.join(output_dir, os.path.basename(output_files[0]))
        
        return None

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
        logger.error("faster-whisper is not installed. Please install it with: pip install faster-whisper")
        return []
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return []

def main():
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description='Preprocess audio files using audio-separator to extract vocals only and transcribe the vocals with timestamped transcription using faster-whisper.')
    parser.add_argument('file_path', nargs='?',
                        help='Path to the input audio file')
    parser.add_argument('--output-dir', '-o', default="output",
                        help='Directory to save the separated audio files (default: output)')
    parser.add_argument('--model', '-m', default="UVR_MDXNET_Main.onnx",
                        help='Model to use for separation (default: UVR_MDXNET_Main.onnx)')
    parser.add_argument('--whisper-model', default="large-v3",
                        help='Whisper model size to use for transcription (default: large-v3)')
    parser.add_argument('--device', default="cpu",
                        help='Device to run the transcription model on (default: cpu)')
    parser.add_argument('--compute-type', default="int8",
                        help='Type of computation to use for transcription (default: int8)')
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
        
        # Transcribe the vocals with timestamps
        logger.info("\nStarting transcription with timestamps...")
        
        if os.path.exists(vocals_file):
            segments = transcribe_with_timestamps(
                vocals_file,
                model_size=args.whisper_model,
                device=args.device,
                compute_type=args.compute_type
            )
        else:
            logger.error(f"Vocals file not found: {vocals_file}")
            segments = []
        
        if segments:
            logger.info(f"\nTranscription completed with {len(segments)} segments.")
            
            # Optionally, save the transcription to a file
            transcript_file = vocals_file.replace('.wav', '_transcript.txt')
            # Create directory if it doesn't exist
            transcript_dir = os.path.dirname(transcript_file)
            if transcript_dir:
                os.makedirs(transcript_dir, exist_ok=True)
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write("Timestamped Transcription:\n\n")
                for segment in segments:
                    f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
            logger.info(f"Transcription saved to: {transcript_file}")
        else:
            logger.error("Transcription failed.")
    else:
        logger.error("Failed to extract vocals")

if __name__ == "__main__":
    main()