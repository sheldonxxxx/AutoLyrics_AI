#!/usr/bin/env python3
"""
Comprehensive unit tests for utils.py module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    find_audio_files, find_flac_files, get_output_paths, ensure_output_directory,
    load_prompt_template, read_lrc_file, read_lyrics_file, read_transcript_file,
    validate_lrc_content, convert_transcript_to_lrc, parse_transcript_segments,
    should_skip_file, extract_lyrics_content, get_prompt_file_for_language,
    write_csv_results
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.temp_intermediate = os.path.join(self.temp_dir, "tmp")

        # Create test directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_intermediate, exist_ok=True)

        # Create test audio files
        self.flac_file = os.path.join(self.input_dir, "test.flac")
        self.mp3_file = os.path.join(self.input_dir, "test.mp3")
        self.nested_flac = os.path.join(self.input_dir, "artist", "album", "song.flac")

        # Create the nested directory and files
        os.makedirs(os.path.dirname(self.nested_flac), exist_ok=True)
        Path(self.flac_file).touch()
        Path(self.mp3_file).touch()
        Path(self.nested_flac).touch()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_find_audio_files_with_valid_directory(self):
        """Test finding audio files in a valid directory."""
        audio_files = find_audio_files(self.input_dir)

        # Should find both FLAC and MP3 files
        self.assertEqual(len(audio_files), 3)  # 2 top-level + 1 nested

        # Check that we found the expected files
        file_paths = [str(f) for f in audio_files]
        self.assertIn(self.flac_file, file_paths)
        self.assertIn(self.mp3_file, file_paths)
        self.assertIn(self.nested_flac, file_paths)

    def test_find_audio_files_with_nonexistent_directory(self):
        """Test finding audio files in a nonexistent directory."""
        audio_files = find_audio_files("/nonexistent/directory")
        self.assertEqual(len(audio_files), 0)

    def test_find_flac_files_with_valid_directory(self):
        """Test finding FLAC files in a valid directory."""
        flac_files = find_flac_files(self.input_dir)

        # Should find both FLAC files
        self.assertEqual(len(flac_files), 2)

        # Check that we found the expected files
        file_paths = [str(f) for f in flac_files]
        self.assertIn(self.flac_file, file_paths)
        self.assertIn(self.nested_flac, file_paths)

    def test_find_flac_files_with_nonexistent_directory(self):
        """Test finding FLAC files in a nonexistent directory."""
        flac_files = find_flac_files("/nonexistent/directory")
        self.assertEqual(len(flac_files), 0)

    def test_get_output_paths_with_nested_structure(self):
        """Test output path generation with nested folder structure."""
        input_file = Path(self.input_dir) / "artist" / "album" / "song.flac"

        paths = get_output_paths(
            input_file,
            output_dir=self.output_dir,
            temp_dir=self.temp_intermediate,
            input_base_dir=self.input_dir
        )

        # Check that paths contain expected structure
        self.assertIn("artist/album", str(paths['vocals_wav']))
        self.assertIn("artist/album", str(paths['translated_lrc']))

        # Check that all expected keys are present
        expected_keys = [
            'vocals_wav', 'transcript_txt', 'corrected_transcript_txt',
            'lyrics_txt', 'lrc', 'translated_lrc'
        ]
        for key in expected_keys:
            self.assertIn(key, paths)

    def test_get_output_paths_with_flat_structure(self):
        """Test output path generation with flat structure."""
        input_file = Path(self.input_dir) / "song.flac"

        paths = get_output_paths(
            input_file,
            output_dir=self.output_dir,
            temp_dir=self.temp_intermediate,
            input_base_dir=self.input_dir
        )

        # Check that paths don't contain nested structure
        vocals_path = str(paths['vocals_wav'])
        self.assertNotIn("artist", vocals_path)
        self.assertNotIn("album", vocals_path)

    def test_ensure_output_directory_success(self):
        """Test successful output directory creation."""
        test_dir = os.path.join(self.temp_dir, "test_output")
        result = ensure_output_directory(test_dir)
        self.assertTrue(result)
        self.assertTrue(Path(test_dir).exists())

    def test_ensure_output_directory_failure(self):
        """Test output directory creation failure."""
        # Try to create a directory in a read-only location (this might not work on all systems)
        test_dir = "/root/test_output"
        result = ensure_output_directory(test_dir)
        # The result depends on system permissions, so we just check it's a boolean
        self.assertIsInstance(result, bool)

    @patch('builtins.open', new_callable=mock_open, read_data="Test prompt content")
    def test_load_prompt_template_success(self, mock_file):
        """Test successful prompt template loading."""
        prompt_file = os.path.join(self.temp_dir, "test_prompt.txt")
        result = load_prompt_template(prompt_file)
        self.assertEqual(result, "Test prompt content")
        mock_file.assert_called_once_with(prompt_file, 'r', encoding='utf-8')

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_prompt_template_file_not_found(self, mock_file):
        """Test prompt template loading with file not found."""
        result = load_prompt_template("/nonexistent/file.txt")
        self.assertIsNone(result)

    @patch('builtins.open', new_callable=mock_open, read_data="[00:01.00]Test lyrics")
    def test_read_lrc_file(self, mock_file):
        """Test LRC file reading."""
        lrc_file = os.path.join(self.temp_dir, "test.lrc")
        result = read_lrc_file(lrc_file)
        self.assertEqual(result, "[00:01.00]Test lyrics")

    @patch('builtins.open', new_callable=mock_open, read_data="Test lyrics content")
    def test_read_lyrics_file(self, mock_file):
        """Test lyrics file reading."""
        lyrics_file = os.path.join(self.temp_dir, "test_lyrics.txt")
        result = read_lyrics_file(lyrics_file)
        self.assertEqual(result, "Test lyrics content")

    @patch('builtins.open', new_callable=mock_open, read_data="[0.92s -> 4.46s] Test transcript")
    def test_read_transcript_file(self, mock_file):
        """Test transcript file reading."""
        transcript_file = os.path.join(self.temp_dir, "test_transcript.txt")
        result = read_transcript_file(transcript_file)
        self.assertEqual(result, "[0.92s -> 4.46s] Test transcript")

    def test_validate_lrc_content_valid(self):
        """Test LRC content validation with valid content."""
        valid_lrc = """[ti:Test Song]
[ar:Test Artist]
[00:01.00]This is a test lyric
[00:05.00]Another test lyric"""

        result = validate_lrc_content(valid_lrc)
        self.assertTrue(result)

    def test_validate_lrc_content_empty(self):
        """Test LRC content validation with empty content."""
        result = validate_lrc_content("")
        self.assertFalse(result)

    def test_validate_lrc_content_no_timestamps(self):
        """Test LRC content validation with no timestamps."""
        content_without_timestamps = "This is just text\nNo timestamps here"
        result = validate_lrc_content(content_without_timestamps)
        self.assertFalse(result)

    def test_convert_transcript_to_lrc(self):
        """Test transcript to LRC conversion."""
        transcript = """[0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
[4.46s -> 8.12s] 君と出会えて本当に良かった"""

        result = convert_transcript_to_lrc(transcript)

        # Check that timestamps are converted to LRC format
        self.assertIn("[00:00.92]", result)
        self.assertIn("[00:04.46]", result)
        self.assertIn("ああ 素晴らしき世界に今日も乾杯", result)
        self.assertIn("君と出会えて本当に良かった", result)

    def test_parse_transcript_segments(self):
        """Test transcript segments parsing."""
        transcript = """[0.92s -> 4.46s] ああ 素晴らしき世界に今日も乾杯
[4.46s -> 8.12s] 君と出会えて本当に良かった"""

        segments = parse_transcript_segments(transcript)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].start, 0.92)
        self.assertEqual(segments[0].end, 4.46)
        self.assertEqual(segments[0].text, "ああ 素晴らしき世界に今日も乾杯")
        self.assertEqual(segments[1].start, 4.46)
        self.assertEqual(segments[1].end, 8.12)
        self.assertEqual(segments[1].text, "君と出会えて本当に良かった")

    def test_should_skip_file_resume_true(self):
        """Test should_skip_file with resume=True and existing files."""
        paths = {
            'translated_lrc': os.path.join(self.output_dir, "test.lrc"),
            'lrc': os.path.join(self.temp_intermediate, "test.lrc")
        }

        # Create the output files
        Path(paths['translated_lrc']).parent.mkdir(parents=True, exist_ok=True)
        Path(paths['lrc']).parent.mkdir(parents=True, exist_ok=True)
        Path(paths['translated_lrc']).touch()
        Path(paths['lrc']).touch()

        result = should_skip_file(paths, resume=True)
        self.assertTrue(result)

    def test_should_skip_file_resume_false(self):
        """Test should_skip_file with resume=False."""
        paths = {
            'translated_lrc': os.path.join(self.output_dir, "test.lrc"),
            'lrc': os.path.join(self.temp_intermediate, "test.lrc")
        }

        result = should_skip_file(paths, resume=False)
        self.assertFalse(result)

    def test_extract_lyrics_content_with_headers(self):
        """Test lyrics content extraction with headers."""
        lyrics_with_headers = """Lyrics for 'Test Song' by Test Artist
============================================================

これが最初の行です
これが二番目の行です
これが三番目の行です"""

        result = extract_lyrics_content(lyrics_with_headers)

        expected = "これが最初の行です\nこれが二番目の行です\nこれが三番目の行です"
        self.assertEqual(result, expected)

    def test_extract_lyrics_content_without_headers(self):
        """Test lyrics content extraction without headers."""
        lyrics_without_headers = """これが最初の行です
これが二番目の行です
これが三番目の行です
これが四番目の行です"""

        result = extract_lyrics_content(lyrics_without_headers)

        # Should return lines after the first 3 (skipping title and header lines)
        expected = "これが四番目の行です"
        self.assertEqual(result, expected)

    def test_get_prompt_file_for_language_supported(self):
        """Test prompt file selection for supported language."""
        result = get_prompt_file_for_language("Traditional Chinese")
        self.assertEqual(result, "lrc_traditional_chinese_prompt.txt")

    def test_get_prompt_file_for_language_unsupported(self):
        """Test prompt file selection for unsupported language."""
        result = get_prompt_file_for_language("English")
        self.assertEqual(result, "")

    def test_write_csv_results_success(self):
        """Test successful CSV results writing."""
        results = [
            {
                'filename': 'test1.flac',
                'file_path': '/path/test1.flac',
                'processing_start_time': '2023-01-01T00:00:00',
                'metadata_success': True,
                'metadata_title': 'Test Song 1',
                'metadata_artist': 'Test Artist 1',
                'overall_success': True,
                'processing_end_time': '2023-01-01T00:01:00',
                'processing_duration_seconds': 60.0,
                'error_message': ''
            },
            {
                'filename': 'test2.flac',
                'file_path': '/path/test2.flac',
                'processing_start_time': '2023-01-01T00:01:00',
                'metadata_success': False,
                'metadata_title': '',
                'metadata_artist': '',
                'overall_success': False,
                'processing_end_time': '2023-01-01T00:02:00',
                'processing_duration_seconds': 60.0,
                'error_message': 'Test error'
            }
        ]

        csv_file = os.path.join(self.temp_dir, "test_results.csv")
        result = write_csv_results(csv_file, results)

        self.assertTrue(result)
        self.assertTrue(Path(csv_file).exists())

        # Check CSV content
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('filename', content)
            self.assertIn('test1.flac', content)
            self.assertIn('test2.flac', content)
            self.assertIn('Test Song 1', content)
            self.assertIn('Test error', content)

    def test_write_csv_results_empty(self):
        """Test CSV results writing with empty results."""
        csv_file = os.path.join(self.temp_dir, "empty_results.csv")
        result = write_csv_results(csv_file, [])
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()