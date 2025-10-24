#!/usr/bin/env python3
"""
Transcribe vocals with timestamped transcription using stable-ts.

This module handles ASR transcription for the Music Lyrics Processing Pipeline.
For comprehensive documentation, see: docs/modules/transcribe_vocals.md

Key Features:
- Multiple Whisper model sizes (tiny to large-v3)
- Word-level timestamp accuracy with stable-ts improvements
- MLX support for Apple Silicon optimization
- CPU-compatible processing with enhanced stability
- Configurable accuracy vs. speed trade-offs

Dependencies:
- stable-ts[mlx] (Stable Transcription with MLX support)
- logging_config (pipeline logging)

Model Sizes: tiny, base, small, medium, large-v1/v2/v3, large-v3-turbo

Pipeline Stage: 3/6 (ASR Transcription)
"""

import os
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger
from ffmpeg_normalize import FFmpegNormalize
import stable_whisper
from stable_whisper.audio import load_audio
from typing import List
from utils import find_audio_files, get_base_argparser, get_output_paths

logger = get_logger(__name__)

class Segment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


def _is_mlx_available():
    """Check if MLX components are available for use."""
    try:
        # Try to import mlx_whisper package directly
        import mlx_whisper

        return True
    except ImportError:
        return False


def detect_language(model, audio, start=30, duration=30):
    """
    Detect the language of the audio using a segment.

    Args:
        model: The Whisper model instance
        audio: The loaded audio data
        start (int): Start time in seconds for the segment to analyze
        duration (int): Duration in seconds for the segment to analyze

    Returns:
        str: Detected language code
    """
    start_samples = start * stable_whisper.whisper_compatibility.SAMPLE_RATE
    end_samples = start_samples + duration * stable_whisper.whisper_compatibility.SAMPLE_RATE

    # Ensure start and end are within audio bounds
    audio_length = len(audio)
    start_samples = max(0, min(start_samples, audio_length - 1))
    end_samples = max(start_samples + 1, min(end_samples, audio_length))

    if end_samples <= start_samples:
        logger.warning(f"Invalid segment: start={start_samples}, end={end_samples}")
        return "en"  # Default fallback

    return model.transcribe(
        audio[start_samples:end_samples], language=None, verbose=None, only_voice_freq=True
    ).language


def _load_transcription_model(model_size, device, use_mlx):
    """Load the appropriate Whisper model based on device and MLX preference."""
    if use_mlx and device == "cpu":
        logger.info(f"Loading MLX Whisper model: {model_size}")
        return stable_whisper.load_mlx_whisper(model_size)
    else:
        logger.info(f"Loading standard Whisper model: {model_size} on {device}")
        return stable_whisper.load_model(model_size, device=device)


def _detect_language_from_segments(model, audio):
    """Detect language using multiple audio segments for robustness."""
    languages = []
    audio_duration = len(audio) / stable_whisper.whisper_compatibility.SAMPLE_RATE
    if audio_duration <= 0:
        logger.warning("Audio duration is zero or negative, skipping language detection")
        return None

    segment_starts = [
        max(0, int(audio_duration * frac) - 5) for frac in [0.3, 0.5, 0.7, 0.9]
    ]
    for start in segment_starts:
        lang = detect_language(model, audio, start=start, duration=15)
        languages.append(lang)
        logger.debug(f"Detected language '{lang}' from segment starting at {start}s")

    if languages:
        detected_language = max(set(languages), key=languages.count)
        logger.info(f"Final detected language: {detected_language}")
        return detected_language
    else:
        logger.warning("No language detected")
        return None


def _process_transcription_result(result):
    """Process the transcription result into segment list with words."""
    segment_list = []
    for segment in result.segments:
        seg = Segment(segment.start, segment.end, segment.text)

        if hasattr(segment, "words") and segment.words:
            seg.words = [Segment(word.start, word.end, word.word) for word in segment.words]
        else:
            seg.words = [seg]  # Fallback

        segment_list.append(seg)
    return segment_list


def _save_transcription(segment_list, transcript_file, transcript_word_file):
    """Save transcription to text files."""
    with open(transcript_file, "w", encoding="utf-8") as f:
        with open(transcript_word_file, "w", encoding="utf-8") as word_f:
            for segment in segment_list:
                if hasattr(segment, "words") and segment.words:
                    for word in segment.words:
                        word_f.write(f"[{word.start:.2f}s -> {word.end:.2f}s] {word.text}\n")
                f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")
    logger.info(f"Transcription saved to: {transcript_file}")


def transcribe_with_timestamps(
    audio_file_path: Path,
    paths: dict,
    model_size="large-v3",
    device="cpu",
    use_mlx=None,
) -> bool:
    """
    Transcribe an audio file with timestamped transcription using stable-ts.

    Args:
        audio_file_path (Path): Path to the audio file to transcribe
        model_size (str): Size of the Whisper model to use (default: "large-v3")
        device (str): Device to run the model on (default: "cpu")
        use_mlx (bool or None): Whether to use MLX models for Apple Silicon.
                                If None, auto-detect based on MLX availability (default: None)

    Returns:
        bool: True if transcription was successful, False otherwise
    """
    try:
        # Set HF_HOME for model downloads
        os.environ["HF_HOME"] = os.path.abspath("./models/huggingface")

        # Auto-detect MLX usage if not explicitly specified
        have_mlx = _is_mlx_available()
        if use_mlx is None and have_mlx:
            use_mlx = True
            logger.info("MLX components detected, using MLX models for optimization")
        elif use_mlx and not have_mlx:
            logger.error(
                "Please install stable-ts with MLX support using: uv add stable-ts[mlx]"
            )
            return False

        # Load the model
        model = _load_transcription_model(model_size, device, use_mlx)

        audio = load_audio(str(audio_file_path))

        # Detect language
        language = _detect_language_from_segments(model, audio)

        # Transcribe the audio
        logger.info(f"Starting transcription of: {audio_file_path}")
        result = model.transcribe(
            audio,
            language=language,
            word_timestamps=True,
            regroup=True,
            vad=True,
            denoiser="demucs",
            suppress_silence=True,
            suppress_word_ts=True,
            verbose=None,
            condition_on_previous_text=False,
            hallucination_silence_threshold=2.0,
        )

        # Process the result
        segment_list = _process_transcription_result(result)

        # Log segments
        for segment in segment_list:
            logger.debug(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

        logger.info(f"Transcription completed with {len(segment_list)} segments")

        # Save the transcription
        transcript_file = paths["transcript_txt"]
        transcript_word_file = paths["transcript_word_txt"]
        _save_transcription(segment_list, transcript_file, transcript_word_file)

        return True
    except Exception:
        logger.exception("Error during transcription")
        return False


def normalize_audio(audio_path: Path, normalized_path: Path) -> bool:
    """
    Normalize audio file to 48kHz WAV format using FFmpegNormalize.

    Args:
        audio_path (Path): Path to the input audio file
        normalized_path (Path): Path for the normalized output file

    Returns:
        bool: True if normalization was successful, False otherwise
    """
    logger = get_logger(__name__)

    try:
        # Create output directory if it doesn't exist
        normalized_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize FFmpegNormalize with specified parameters
        normalizer = FFmpegNormalize(
            output_format="wav",
            sample_rate=48000,
            progress=False,
            keep_lra_above_loudness_range_target=True,
            target_level=-16.0,
            audio_channels=1,
        )

        # Add the audio file for normalization
        normalizer.add_media_file(str(audio_path), str(normalized_path))

        # Run normalization
        logger.info(f"Normalizing audio: {audio_path} -> {normalized_path}")
        normalizer.run_normalization()

        # Check if normalized file was created successfully
        if normalized_path.exists():
            logger.info(
                f"Audio normalization completed successfully: {normalized_path}"
            )
            return True
        else:
            logger.error(
                f"Normalization failed - output file not found: {normalized_path}"
            )
            return False

    except ImportError:
        logger.exception(
            "ffmpeg-normalize is not installed. Please install it with: pip install ffmpeg-normalize"
        )
        return False
    except Exception as e:
        logger.exception(f"Error during audio normalization: {e}")
        return False


def process_single_file(input_file: Path, output_dir: Path, args) -> bool:
    """
    Process a single audio file for transcription.

    Args:
        input_file (Path): Path to the input audio file
        output_dir (Path): Directory for output files
        args: Parsed command line arguments

    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger.info(f"Starting transcription for: {input_file}")

    # Handle normalization if requested
    audio_file_to_transcribe = input_file
    if args.normalize:
        output_path = output_dir / input_file.name.replace(
            input_file.suffix, "_normalized.wav"
        )
        if not normalize_audio(input_file, output_path):
            logger.error(f"Audio normalization failed for {input_file}")
            return False

        audio_file_to_transcribe = output_path
        logger.info(
            f"Using normalized audio file for transcription: {audio_file_to_transcribe}"
        )

    paths = get_output_paths(input_file, output_dir)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Transcribe the vocals with timestamps
        transcribe_with_timestamps(
            audio_file_to_transcribe,
            paths,
            model_size=args.model,
            device=args.device,
            use_mlx=args.use_mlx,
        )
        return True
    except Exception:
        logger.exception(f"Error processing file {input_file}")
        return False

def process_batch(input_dir: Path, output_dir: Path, args) -> int:
    """
    Process all audio files in a directory.

    Args:
        input_dir (Path): Directory containing audio files
        output_dir (Path): Directory for output files
        args: Parsed command line arguments

    Returns:
        int: Number of files successfully processed
    """
    logger.info(f"Starting batch processing for directory: {input_dir}")

    # Find audio files using the utility function
    audio_files = find_audio_files(str(input_dir))

    if not audio_files:
        logger.warning(f"No audio files found in {input_dir}")
        return 0

    # Process each file
    successful = 0
    failed = 0

    for audio_file in audio_files:
        logger.info(
            f"Processing file {successful + failed + 1}/{len(audio_files)}: {audio_file.name}"
        )

        # Create subdirectory structure if needed
        relative_path = audio_file.relative_to(input_dir)
        file_output_dir = output_dir / relative_path.parent
        file_output_dir.mkdir(parents=True, exist_ok=True)

        if process_single_file(audio_file, file_output_dir, args):
            successful += 1
        else:
            failed += 1

    logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
    return successful


def main():
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    # Set up argument parser
    parser = get_base_argparser(
        description="Transcribe vocals with timestamped transcription using stable-ts."
    )

    parser.add_argument(
        "input_path",
        help="Path to input audio file or directory containing audio files",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        help="Output directory for transcript files (default: same as input)",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Enable audio normalization to 48kHz WAV before transcription",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively search subdirectories for audio files (only used when input is a directory)",
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        help="Whisper model size to use for transcription (default: large-v3)",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device to run the transcription model on (default: cpu)",
    )
    parser.add_argument(
        "--use-mlx",
        action="store_true",
        help="Use MLX models if available (auto-detected if not specified)",
    )

    args = parser.parse_args()

    # Set up logging with specified level
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level, enable_logfire=args.logfire)

    # Define the input path
    input_path = Path(args.input_path)

    # Check if the input path exists
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent if input_path.is_file() else input_path

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process single file or batch
    if input_path.is_file():
        # Single file processing
        success = process_single_file(input_path, output_dir, args)
        if not success:
            exit(1)
    else:
        # Batch processing
        successful_count = process_batch(input_path, output_dir, args)
        if successful_count == 0:
            logger.error("No files were successfully processed")
            exit(1)


if __name__ == "__main__":
    main()
