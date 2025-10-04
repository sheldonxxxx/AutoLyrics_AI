#!/usr/bin/env python3
"""
Integration tests for process_lyrics.py module.
"""

import unittest
import tempfile
import shutil
import os
import sys
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process_lyrics import (
    ProcessingResults, extract_metadata_step, separate_vocals_step,
    transcribe_vocals_step, search_lyrics_step, grammatical_correction_step,
    generate_lrc_step, translate_lrc_step, process_single_audio_file
)


class TestProcessLyricsIntegration(unittest.TestCase):
    """Integration test cases for the lyrics processing pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "test_song.flac")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.temp_intermediate = os.path.join(self.temp_dir, "tmp")

        # Create test input file
        with open(self.input_file, 'wb') as f:
            f.write(b'fake audio content')

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_intermediate, exist_ok=True)

        # Create test paths
        self.paths = {
            'vocals_wav': os.path.join(self.temp_intermediate, "test_song_(Vocals)_UVR_MDXNET_Main.wav"),
            'transcript_txt': os.path.join(self.temp_intermediate, "test_song_(Vocals)_UVR_MDXNET_Main_transcript.txt"),
            'corrected_transcript_txt': os.path.join(self.temp_intermediate, "test_song_(Vocals)_UVR_MDXNET_Main_corrected_transcript.txt"),
            'lyrics_txt': os.path.join(self.temp_intermediate, "test_song_lyrics.txt"),
            'lrc': os.path.join(self.temp_intermediate, "test_song.lrc"),
            'translated_lrc': os.path.join(self.output_dir, "test_song.lrc")
        }

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_processing_results_initialization(self):
        """Test ProcessingResults initialization."""
        start_time = time.time()
        results = ProcessingResults(Path(self.input_file), start_time)

        # Check initial values
        self.assertEqual(results.input_file, Path(self.input_file))
        self.assertEqual(results.start_time, start_time)
        self.assertEqual(results.filename, "test_song.flac")
        self.assertEqual(results.file_path, self.input_file)

        # Check that all step results are initialized to False/None
        self.assertFalse(results.metadata_success)
        self.assertFalse(results.vocals_separation_success)
        self.assertFalse(results.transcription_success)
        self.assertFalse(results.lyrics_search_success)
        self.assertFalse(results.grammatical_correction_success)
        self.assertFalse(results.lrc_generation_success)
        self.assertFalse(results.translation_success)
        self.assertFalse(results.overall_success)

        # Check that empty values are set correctly
        self.assertIsNone(results.metadata_title)
        self.assertIsNone(results.metadata_artist)
        self.assertEqual(results.vocals_file_path, '')
        self.assertEqual(results.error_message, '')

    def test_processing_results_to_dict(self):
        """Test ProcessingResults to_dict conversion."""
        results = ProcessingResults(Path(self.input_file), time.time())
        results.metadata_success = True
        results.metadata_title = "Test Song"
        results.metadata_artist = "Test Artist"
        results.overall_success = True

        result_dict = results.to_dict()

        # Check that all expected keys are present
        expected_keys = [
            'filename', 'file_path', 'processing_start_time', 'metadata_success',
            'metadata_title', 'metadata_artist', 'overall_success', 'error_message'
        ]

        for key in expected_keys:
            self.assertIn(key, result_dict)

        # Check that our test values are present
        self.assertEqual(result_dict['metadata_success'], True)
        self.assertEqual(result_dict['metadata_title'], "Test Song")
        self.assertEqual(result_dict['metadata_artist'], "Test Artist")
        self.assertEqual(result_dict['overall_success'], True)

    def test_processing_results_finalize(self):
        """Test ProcessingResults finalize method."""
        start_time = time.time()
        results = ProcessingResults(Path(self.input_file), start_time)

        # Sleep briefly to ensure different end time
        time.sleep(0.01)
        results.finalize()

        # Check that timing information was set
        self.assertIsNotNone(results.processing_end_time)
        self.assertGreater(results.processing_duration_seconds, 0)
        self.assertGreater(results.processing_duration_seconds, time.time() - start_time - 0.1)  # Allow some margin

    @patch('process_lyrics.extract_metadata')
    def test_extract_metadata_step_success(self, mock_extract_metadata):
        """Test successful metadata extraction step."""
        # Mock successful metadata extraction
        mock_extract_metadata.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'genre': 'Pop',
            'year': '2023',
            'track_number': '1'
        }

        results = ProcessingResults(Path(self.input_file), time.time())

        success = extract_metadata_step(Path(self.input_file), results)

        # Check that step was successful
        self.assertTrue(success)
        self.assertTrue(results.metadata_success)
        self.assertEqual(results.metadata_title, 'Test Song')
        self.assertEqual(results.metadata_artist, 'Test Artist')
        self.assertEqual(results.metadata_album, 'Test Album')
        self.assertEqual(results.metadata_genre, 'Pop')
        self.assertEqual(results.metadata_year, '2023')
        self.assertEqual(results.metadata_track_number, '1')

    @patch('process_lyrics.extract_metadata')
    def test_extract_metadata_step_failure(self, mock_extract_metadata):
        """Test failed metadata extraction step."""
        # Mock metadata extraction to raise exception
        mock_extract_metadata.side_effect = Exception("Metadata extraction failed")

        results = ProcessingResults(Path(self.input_file), time.time())

        success = extract_metadata_step(Path(self.input_file), results)

        # Check that step failed
        self.assertFalse(success)
        self.assertFalse(results.metadata_success)
        self.assertIn("Metadata extraction failed", results.error_message)

    @patch('process_lyrics.separate_vocals')
    def test_separate_vocals_step_success(self, mock_separate_vocals):
        """Test successful vocal separation step."""
        # Mock successful vocal separation
        mock_separate_vocals.return_value = "/path/to/vocals.wav"

        results = ProcessingResults(Path(self.input_file), time.time())

        success = separate_vocals_step(Path(self.input_file), self.paths, False, results, self.temp_intermediate)

        # Check that step was successful
        self.assertTrue(success)
        self.assertTrue(results.vocals_separation_success)
        self.assertEqual(results.vocals_file_path, "/path/to/vocals.wav")

        # Check that separate_vocals was called with correct parameters
        mock_separate_vocals.assert_called_once_with(
            str(Path(self.input_file)),
            output_dir=self.temp_intermediate
        )

    @patch('process_lyrics.separate_vocals')
    def test_separate_vocals_step_resume_with_existing_file(self, mock_separate_vocals):
        """Test vocal separation step with resume and existing file."""
        # Create existing vocals file
        vocals_path = Path(self.paths['vocals_wav'])
        vocals_path.parent.mkdir(parents=True, exist_ok=True)
        vocals_path.touch()

        results = ProcessingResults(Path(self.input_file), time.time())

        success = separate_vocals_step(Path(self.input_file), self.paths, True, results, self.temp_intermediate)

        # Check that step was successful (used existing file)
        self.assertTrue(success)
        self.assertTrue(results.vocals_separation_success)

        # Check that separate_vocals was not called (used existing file)
        mock_separate_vocals.assert_not_called()

    @patch('process_lyrics.transcribe_with_timestamps')
    def test_transcribe_vocals_step_success(self, mock_transcribe):
        """Test successful vocal transcription step."""
        # Mock successful transcription
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 3.5
        mock_segment.text = "これはテストのトランスクリプトです"
        mock_transcribe.return_value = [mock_segment]

        results = ProcessingResults(Path(self.input_file), time.time())
        results.vocals_file_path = "/path/to/vocals.wav"

        segments = transcribe_vocals_step("/path/to/vocals.wav", self.paths, False, results)

        # Check that step was successful
        self.assertIsNotNone(segments)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "これはテストのトランスクリプトです")
        self.assertTrue(results.transcription_success)
        self.assertEqual(results.transcription_segments_count, 1)

        # Check that transcribe_with_timestamps was called
        mock_transcribe.assert_called_once_with("/path/to/vocals.wav")

    @patch('process_lyrics.transcribe_with_timestamps')
    def test_transcribe_vocals_step_resume_with_existing_file(self, mock_transcribe):
        """Test vocal transcription step with resume and existing file."""
        # Create existing transcript file
        transcript_path = Path(self.paths['transcript_txt'])
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("[0.0s -> 3.5s] 既存のトランスクリプト")

        results = ProcessingResults(Path(self.input_file), time.time())
        results.vocals_file_path = "/path/to/vocals.wav"

        segments = transcribe_vocals_step("/path/to/vocals.wav", self.paths, True, results)

        # Check that existing transcript was loaded
        self.assertIsNotNone(segments)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "既存のトランスクリプト")

        # Check that transcribe_with_timestamps was not called
        mock_transcribe.assert_not_called()

    @patch('process_lyrics.search_uta_net')
    def test_search_lyrics_step_success(self, mock_search_lyrics):
        """Test successful lyrics search step."""
        # Mock successful lyrics search
        mock_search_lyrics.return_value = "これはテストの歌詞です\n二番目の行です"

        metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'genre': 'Pop',
            'year': '2023',
            'track_number': '1'
        }

        results = ProcessingResults(Path(self.input_file), time.time())

        lyrics_content = search_lyrics_step(metadata, self.paths, False, results)

        # Check that step was successful
        self.assertIsNotNone(lyrics_content)
        self.assertIn("これはテストの歌詞です", lyrics_content)
        self.assertTrue(results.lyrics_search_success)
        self.assertEqual(results.lyrics_source, 'uta-net.com')
        self.assertEqual(results.lyrics_length, len(lyrics_content))
        self.assertGreater(results.lyrics_line_count, 0)

    @patch('process_lyrics.search_uta_net')
    def test_search_lyrics_step_no_lyrics_found(self, mock_search_lyrics):
        """Test lyrics search step when no lyrics found."""
        # Mock lyrics search returning None
        mock_search_lyrics.return_value = None

        metadata = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'genre': 'Pop',
            'year': '2023',
            'track_number': '1'
        }

        results = ProcessingResults(Path(self.input_file), time.time())

        lyrics_content = search_lyrics_step(metadata, self.paths, False, results)

        # Check that step failed gracefully
        self.assertIsNone(lyrics_content)
        self.assertFalse(results.lyrics_search_success)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key', 'OPENAI_BASE_URL': 'https://test.api.com'})
    @patch('process_lyrics.OpenAI')
    @patch('process_lyrics.correct_grammar_in_transcript')
    def test_grammatical_correction_step_success(self, mock_correct_grammar, mock_openai_class):
        """Test successful grammatical correction step."""
        # Mock successful grammatical correction
        mock_correct_grammar.return_value = "これは修正されたトランスクリプトです"

        # Create existing transcript file
        transcript_path = Path(self.paths['transcript_txt'])
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("[0.0s -> 3.5s] これはまちがったとらんすくりぷとです")

        results = ProcessingResults(Path(self.input_file), time.time())

        corrected_content = grammatical_correction_step(self.paths, False, results)

        # Check that step was successful
        self.assertIsNotNone(corrected_content)
        self.assertIn("これは修正されたトランスクリプトです", corrected_content)
        self.assertTrue(results.grammatical_correction_success)
        self.assertTrue(results.grammatical_correction_applied)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('process_lyrics.OpenAI')
    @patch('process_lyrics.correct_grammar_in_transcript')
    def test_grammatical_correction_step_no_correction_needed(self, mock_correct_grammar, mock_openai_class):
        """Test grammatical correction step when no correction is needed."""
        # Mock correction that returns same as input
        mock_correct_grammar.return_value = "これは既に正しいトランスクリプトです"

        # Create existing transcript file
        transcript_path = Path(self.paths['transcript_txt'])
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("[0.0s -> 3.5s] これは既に正しいトランスクリプトです")

        results = ProcessingResults(Path(self.input_file), time.time())

        corrected_content = grammatical_correction_step(self.paths, False, results)

        # Check that step succeeded but no correction was applied
        self.assertIsNotNone(corrected_content)
        self.assertTrue(results.grammatical_correction_success)
        self.assertFalse(results.grammatical_correction_applied)  # No correction applied

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('process_lyrics.OpenAI')
    @patch('process_lyrics.generate_lrc_lyrics')
    def test_generate_lrc_step_success_with_lyrics(self, mock_generate_lrc, mock_openai_class):
        """Test successful LRC generation step with lyrics."""
        # Mock successful LRC generation
        mock_generate_lrc.return_value = "[00:01.00]これはテストの歌詞です\n[00:05.00]二番目の行です"

        # Create existing transcript file
        transcript_path = Path(self.paths['transcript_txt'])
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("[0.0s -> 3.5s] トランスクリプト")

        results = ProcessingResults(Path(self.input_file), time.time())

        success = generate_lrc_step(
            "これはテストの歌詞です",  # lyrics_content
            None,  # corrected_transcript_content
            str(transcript_path),
            self.paths,
            False,  # resume
            results
        )

        # Check that step was successful
        self.assertTrue(success)
        self.assertTrue(results.lrc_generation_success)
        self.assertGreater(results.lrc_line_count, 0)
        self.assertTrue(results.lrc_has_timestamps)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('process_lyrics.OpenAI')
    @patch('process_lyrics.generate_lrc_lyrics')
    def test_generate_lrc_step_success_with_corrected_transcript(self, mock_generate_lrc, mock_openai_class):
        """Test successful LRC generation step with corrected transcript."""
        # Mock successful LRC generation
        mock_generate_lrc.return_value = "[00:01.00]修正されたトランスクリプト"

        # Create existing transcript file
        transcript_path = Path(self.paths['transcript_txt'])
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("[0.0s -> 3.5s] トランスクリプト")

        results = ProcessingResults(Path(self.input_file), time.time())

        success = generate_lrc_step(
            None,  # lyrics_content (None - no lyrics found)
            "これは修正されたトランスクリプトです",  # corrected_transcript_content
            str(transcript_path),
            self.paths,
            False,  # resume
            results
        )

        # Check that step was successful using corrected transcript
        self.assertTrue(success)
        self.assertTrue(results.lrc_generation_success)

    @patch('process_lyrics.translate_main')
    def test_translate_lrc_step_success(self, mock_translate_main):
        """Test successful LRC translation step."""
        # Mock successful translation
        mock_translate_main.return_value = True

        # Create existing LRC file
        lrc_path = Path(self.paths['lrc'])
        lrc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write("[00:01.00]テスト")

        results = ProcessingResults(Path(self.input_file), time.time())

        success = translate_lrc_step(str(lrc_path), self.paths, False, logging.INFO, results)

        # Check that step was successful
        self.assertTrue(success)
        self.assertTrue(results.translation_success)
        self.assertTrue(results.overall_success)

        # Check that translate_main was called with correct parameters
        mock_translate_main.assert_called_once()
        args = mock_translate_main.call_args[0]
        self.assertEqual(args[0], str(lrc_path))
        self.assertEqual(args[1], self.paths['translated_lrc'])
        self.assertEqual(args[2], "Traditional Chinese")

    @patch('process_lyrics.translate_main')
    def test_translate_lrc_step_resume_with_existing_file(self, mock_translate_main):
        """Test LRC translation step with resume and existing file."""
        # Create existing translated LRC file
        translated_path = Path(self.paths['translated_lrc'])
        translated_path.parent.mkdir(parents=True, exist_ok=True)
        translated_path.touch()

        results = ProcessingResults(Path(self.input_file), time.time())

        success = translate_lrc_step("/path/to/input.lrc", self.paths, True, logging.INFO, results)

        # Check that step was successful (used existing file)
        self.assertTrue(success)

        # Check that translate_main was not called (used existing file)
        mock_translate_main.assert_not_called()

    @patch('process_lyrics.translate_main')
    def test_translate_lrc_step_failure(self, mock_translate_main):
        """Test failed LRC translation step."""
        # Mock failed translation
        mock_translate_main.return_value = False

        # Create existing LRC file
        lrc_path = Path(self.paths['lrc'])
        lrc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write("[00:01.00]テスト")

        results = ProcessingResults(Path(self.input_file), time.time())

        success = translate_lrc_step(str(lrc_path), self.paths, False, logging.INFO, results)

        # Check that step failed
        self.assertFalse(success)
        self.assertFalse(results.translation_success)
        self.assertIn("Translation failed", results.error_message)

    @patch('process_lyrics.extract_metadata')
    @patch('process_lyrics.separate_vocals')
    @patch('process_lyrics.transcribe_with_timestamps')
    @patch('process_lyrics.search_uta_net')
    @patch('process_lyrics.generate_lrc_lyrics')
    @patch('process_lyrics.translate_main')
    def test_process_single_audio_file_full_success(self, mock_translate, mock_generate_lrc,
                                                   mock_search_lyrics, mock_transcribe,
                                                   mock_separate, mock_extract):
        """Test complete successful processing of a single audio file."""
        # Mock all steps to succeed
        mock_extract.return_value = {
            'title': 'Test Song', 'artist': 'Test Artist', 'album': 'Test Album',
            'genre': 'Pop', 'year': '2023', 'track_number': '1'
        }
        mock_separate.return_value = "/path/to/vocals.wav"

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 3.5
        mock_segment.text = "テストトランスクリプト"
        mock_transcribe.return_value = [mock_segment]

        mock_search_lyrics.return_value = "テストの歌詞です"
        mock_generate_lrc.return_value = "[00:01.00]テスト歌詞"
        mock_translate.return_value = True

        success, results_dict = process_single_audio_file(
            Path(self.input_file),
            output_dir=self.output_dir,
            temp_dir=self.temp_intermediate,
            resume=False
        )

        # Check that overall process was successful
        self.assertTrue(success)
        self.assertTrue(results_dict['overall_success'])
        self.assertTrue(results_dict['metadata_success'])
        self.assertTrue(results_dict['vocals_separation_success'])
        self.assertTrue(results_dict['transcription_success'])
        self.assertTrue(results_dict['lyrics_search_success'])
        self.assertTrue(results_dict['lrc_generation_success'])
        self.assertTrue(results_dict['translation_success'])

    @patch('process_lyrics.extract_metadata')
    def test_process_single_audio_file_metadata_failure(self, mock_extract):
        """Test processing failure at metadata step."""
        # Mock metadata extraction to fail
        mock_extract.side_effect = Exception("Metadata error")

        success, results_dict = process_single_audio_file(
            Path(self.input_file),
            output_dir=self.output_dir,
            temp_dir=self.temp_intermediate,
            resume=False
        )

        # Check that process failed at metadata step
        self.assertFalse(success)
        self.assertFalse(results_dict['metadata_success'])
        self.assertFalse(results_dict['overall_success'])
        self.assertIn("Metadata error", results_dict['error_message'])


if __name__ == '__main__':
    unittest.main()