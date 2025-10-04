#!/usr/bin/env python3
"""
Comprehensive unit tests for separate_vocals.py module.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from separate_vocals import separate_vocals, transcribe_with_timestamps


class TestSeparateVocals(unittest.TestCase):
    """Test cases for vocal separation and transcription functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "test_input.flac")
        self.output_dir = os.path.join(self.temp_dir, "output")

        # Create test input file
        with open(self.input_file, 'wb') as f:
            f.write(b'fake audio content')

        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_success_with_vocals_file(self, mock_separator_class):
        """Test successful vocal separation with vocals file found."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator

        # Mock the separate method to return output files including vocals
        mock_separator.separate.return_value = [
            "/path/to/output/(Vocals)_UVR_MDXNET_Main.wav",
            "/path/to/output/(Drums)_UVR_MDXNET_Main.wav",
            "/path/to/output/(Bass)_UVR_MDXNET_Main.wav"
        ]

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that vocals file was found and returned
        expected_path = os.path.join(self.output_dir, "(Vocals)_UVR_MDXNET_Main.wav")
        self.assertEqual(result, expected_path)

        # Check that separator was configured correctly
        mock_separator_class.assert_called_once()
        self.assertEqual(mock_separator.model_file_dir, os.path.join(os.getcwd(), "models"))
        self.assertEqual(mock_separator.output_dir, self.output_dir)
        self.assertEqual(mock_separator.single_stem, "Vocals")
        mock_separator.load_model.assert_called_once_with(model_filename="UVR_MDXNET_Main.onnx")
        mock_separator.separate.assert_called_once_with(self.input_file)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_success_with_vocal_file(self, mock_separator_class):
        """Test successful vocal separation with 'vocal' file found."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator

        # Mock the separate method to return output files with 'vocal' in name
        mock_separator.separate.return_value = [
            "/path/to/output/song_vocal_uvr.wav",
            "/path/to/output/song_drums_uvr.wav"
        ]

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that vocal file was found and returned
        expected_path = os.path.join(self.output_dir, "song_vocal_uvr.wav")
        self.assertEqual(result, expected_path)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_success_with_voice_file(self, mock_separator_class):
        """Test successful vocal separation with 'voice' file found."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator

        # Mock the separate method to return output files with 'voice' in name
        mock_separator.separate.return_value = [
            "/path/to/output/song_voice_separated.wav",
            "/path/to/output/song_music.wav"
        ]

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that voice file was found and returned
        expected_path = os.path.join(self.output_dir, "song_voice_separated.wav")
        self.assertEqual(result, expected_path)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_no_vocal_files_found(self, mock_separator_class):
        """Test vocal separation when no vocal files are found."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator

        # Mock the separate method to return output files without vocals
        mock_separator.separate.return_value = [
            "/path/to/output/song_drums.wav",
            "/path/to/output/song_bass.wav",
            "/path/to/output/song_music.wav"
        ]

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that first available file is returned as fallback
        expected_path = os.path.join(self.output_dir, "song_drums.wav")
        self.assertEqual(result, expected_path)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_empty_output_files(self, mock_separator_class):
        """Test vocal separation with empty output files list."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator

        # Mock the separate method to return empty list
        mock_separator.separate.return_value = []

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that None is returned when no output files
        self.assertIsNone(result)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_with_custom_model(self, mock_separator_class):
        """Test vocal separation with custom model."""
        # Mock separator and its methods
        mock_separator = MagicMock()
        mock_separator_class.return_value = mock_separator
        mock_separator.separate.return_value = ["/path/to/output/(Vocals)_Custom_Model.wav"]

        custom_model = "Custom_Model.onnx"
        result = separate_vocals(self.input_file, output_dir=self.output_dir, model=custom_model)

        # Check that custom model was used
        mock_separator.load_model.assert_called_once_with(model_filename=custom_model)

    @patch('separate_vocals.Separator')
    def test_separate_vocals_separator_exception(self, mock_separator_class):
        """Test vocal separation with separator exception."""
        # Mock separator to raise an exception
        mock_separator_class.side_effect = Exception("Separator error")

        result = separate_vocals(self.input_file, output_dir=self.output_dir)

        # Check that None is returned on exception
        self.assertIsNone(result)

    @patch('separate_vocals.os.makedirs')
    def test_separate_vocals_creates_directories(self, mock_makedirs):
        """Test that vocal separation creates necessary directories."""
        with patch('separate_vocals.Separator') as mock_separator_class:
            # Mock separator
            mock_separator = MagicMock()
            mock_separator_class.return_value = mock_separator
            mock_separator.separate.return_value = ["/path/to/output/(Vocals)_UVR_MDXNET_Main.wav"]

            separate_vocals(self.input_file, output_dir=self.output_dir)

            # Check that directories were created
            mock_makedirs.assert_called()

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_success(self, mock_whisper_class):
        """Test successful transcription with timestamps."""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model

        # Mock segments with timestamps
        mock_segment1 = MagicMock()
        mock_segment1.start = 0.0
        mock_segment1.end = 3.5
        mock_segment1.text = "これは最初のセグメントです"

        mock_segment2 = MagicMock()
        mock_segment2.start = 3.5
        mock_segment2.end = 7.2
        mock_segment2.text = "これは二番目のセグメントです"

        mock_segments = [mock_segment1, mock_segment2]
        mock_model.transcribe.return_value = (mock_segments, None)

        result = transcribe_with_timestamps(self.input_file)

        # Check that segments were returned
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].start, 0.0)
        self.assertEqual(result[0].end, 3.5)
        self.assertEqual(result[0].text, "これは最初のセグメントです")
        self.assertEqual(result[1].start, 3.5)
        self.assertEqual(result[1].end, 7.2)
        self.assertEqual(result[1].text, "これは二番目のセグメントです")

        # Check that model was configured correctly
        mock_whisper_class.assert_called_once_with("large-v3", device="cpu", compute_type="int8")
        mock_model.transcribe.assert_called_once_with(self.input_file, beam_size=5, word_timestamps=True)

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_empty_segments(self, mock_whisper_class):
        """Test transcription with empty segments."""
        # Mock Whisper model with empty segments
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model
        mock_model.transcribe.return_value = ([], None)

        result = transcribe_with_timestamps(self.input_file)

        # Check that empty list is returned
        self.assertEqual(result, [])

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_import_error(self, mock_whisper_class):
        """Test transcription with import error."""
        # Mock ImportError for faster-whisper
        mock_whisper_class.side_effect = ImportError("faster-whisper not installed")

        result = transcribe_with_timestamps(self.input_file)

        # Check that empty list is returned on import error
        self.assertEqual(result, [])

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_general_exception(self, mock_whisper_class):
        """Test transcription with general exception."""
        # Mock Whisper model to raise exception
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model
        mock_model.transcribe.side_effect = Exception("Transcription error")

        result = transcribe_with_timestamps(self.input_file)

        # Check that empty list is returned on exception
        self.assertEqual(result, [])

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_custom_model_size(self, mock_whisper_class):
        """Test transcription with custom model size."""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model
        mock_model.transcribe.return_value = ([], None)

        custom_model_size = "medium"
        transcribe_with_timestamps(self.input_file, model_size=custom_model_size)

        # Check that custom model size was used
        mock_whisper_class.assert_called_once_with(custom_model_size, device="cpu", compute_type="int8")

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_custom_device(self, mock_whisper_class):
        """Test transcription with custom device."""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model
        mock_model.transcribe.return_value = ([], None)

        custom_device = "cuda"
        custom_compute_type = "float16"
        transcribe_with_timestamps(
            self.input_file,
            model_size="large-v3",
            device=custom_device,
            compute_type=custom_compute_type
        )

        # Check that custom device and compute type were used
        mock_whisper_class.assert_called_once_with("large-v3", device=custom_device, compute_type=custom_compute_type)

    @patch('separate_vocals.WhisperModel')
    def test_transcribe_with_timestamps_segments_iteration(self, mock_whisper_class):
        """Test that segments are properly converted to list."""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model

        # Mock segments as iterator
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "テストセグメント"

        mock_segments_iter = iter([mock_segment])
        mock_model.transcribe.return_value = (mock_segments_iter, None)

        result = transcribe_with_timestamps(self.input_file)

        # Check that iterator was converted to list
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].start, 0.0)
        self.assertEqual(result[0].end, 2.0)
        self.assertEqual(result[0].text, "テストセグメント")


if __name__ == '__main__':
    unittest.main()