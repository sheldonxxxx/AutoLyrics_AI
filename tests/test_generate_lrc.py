#!/usr/bin/env python3
"""
Comprehensive unit tests for generate_lrc.py module.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_lrc import generate_lrc_lyrics, correct_grammar_in_transcript


class TestGenerateLRC(unittest.TestCase):
    """Test cases for LRC generation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.lyrics_file = os.path.join(self.temp_dir, "test_lyrics.txt")
        self.transcript_file = os.path.join(self.temp_dir, "test_transcript.txt")
        self.prompt_file = os.path.join(self.temp_dir, "lrc_generation_prompt.txt")

        # Create test content
        with open(self.lyrics_file, 'w', encoding='utf-8') as f:
            f.write("これがテストの歌詞です\nこれが二番目の行です")

        with open(self.transcript_file, 'w', encoding='utf-8') as f:
            f.write("[0.92s -> 4.46s] これがテストのトランスクリプトです")

        with open(self.prompt_file, 'w', encoding='utf-8') as f:
            f.write("Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key', 'OPENAI_MODEL': 'test_model'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_success(self, mock_load_prompt, mock_openai_class):
        """Test successful LRC generation."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[00:01.00]これがテストの歌詞です"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test data
        lyrics_text = "これがテストの歌詞です"
        asr_transcript = "[0.92s -> 4.46s] これがテストのトランスクリプトです"

        result = generate_lrc_lyrics(mock_client, lyrics_text, asr_transcript)

        # Check that LRC was generated successfully
        self.assertIsNotNone(result)
        self.assertIn("[00:01.00]", result)
        self.assertIn("これがテストの歌詞です", result)

        # Check that API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'test_model')
        self.assertEqual(call_args[1]['temperature'], 0.1)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_default_model(self, mock_load_prompt, mock_openai_class):
        """Test LRC generation with default model."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[00:01.00]これがテストの歌詞です"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Remove OPENAI_MODEL from environment to test default
        env = os.environ.copy()
        if 'OPENAI_MODEL' in env:
            del env['OPENAI_MODEL']

        with patch.dict(os.environ, env, clear=True):
            result = generate_lrc_lyrics(mock_client, "test lyrics", "test transcript")

            # Check that default model was used
            call_args = mock_client.chat.completions.create.call_args
            self.assertEqual(call_args[1]['model'], 'Qwen/Qwen3-235B-A22B-Instruct-2507')

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_prompt_template_not_found(self, mock_load_prompt, mock_openai_class):
        """Test LRC generation when prompt template is not found."""
        # Mock prompt template loading to return None
        mock_load_prompt.return_value = None

        mock_client = MagicMock()

        result = generate_lrc_lyrics(mock_client, "test lyrics", "test transcript")

        # Check that None is returned when prompt template not found
        self.assertIsNone(result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_api_exception(self, mock_load_prompt, mock_openai_class):
        """Test LRC generation with API exception."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}"

        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        result = generate_lrc_lyrics(mock_client, "test lyrics", "test transcript")

        # Check that None is returned on API exception
        self.assertIsNone(result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key', 'OPENAI_MODEL': 'test_model'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_success(self, mock_load_prompt, mock_openai_class):
        """Test successful grammatical correction."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Correct grammar in transcript: {asr_transcript} for file: {filename}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "これは文法的に修正されたトランスクリプトです。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test data
        asr_transcript = "これは文法的にまちがったとらんすくりぷとです"

        result = correct_grammar_in_transcript(mock_client, asr_transcript, "test_song.flac")

        # Check that correction was applied
        self.assertIsNotNone(result)
        self.assertEqual(result, "これは文法的に修正されたトランスクリプトです。")
        self.assertNotEqual(result, asr_transcript)  # Should be different from input

        # Check that API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'test_model')
        self.assertEqual(call_args[1]['temperature'], 0.1)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_no_correction_needed(self, mock_load_prompt, mock_openai_class):
        """Test grammatical correction when no correction is needed."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Correct grammar in transcript: {asr_transcript} for file: {filename}"

        # Mock OpenAI client and response (returns same as input)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "これは既に正しいトランスクリプトです。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test data (already correct transcript)
        asr_transcript = "これは既に正しいトランスクリプトです。"

        result = correct_grammar_in_transcript(mock_client, asr_transcript, "test_song.flac")

        # Check that correction was applied (even if same as input)
        self.assertIsNotNone(result)
        self.assertEqual(result, "これは既に正しいトランスクリプトです。")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_prompt_template_not_found(self, mock_load_prompt, mock_openai_class):
        """Test grammatical correction when prompt template is not found."""
        # Mock prompt template loading to return None
        mock_load_prompt.return_value = None

        mock_client = MagicMock()
        asr_transcript = "これはテストのトランスクリプトです"

        result = correct_grammar_in_transcript(mock_client, asr_transcript, "test_song.flac")

        # Check that original transcript is returned when prompt template not found
        self.assertEqual(result, asr_transcript)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_api_exception(self, mock_load_prompt, mock_openai_class):
        """Test grammatical correction with API exception."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Correct grammar in transcript: {asr_transcript} for file: {filename}"

        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        asr_transcript = "これはテストのトランスクリプトです"

        result = correct_grammar_in_transcript(mock_client, asr_transcript, "test_song.flac")

        # Check that original transcript is returned on API exception
        self.assertEqual(result, asr_transcript)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_empty_transcript(self, mock_load_prompt, mock_openai_class):
        """Test grammatical correction with empty transcript."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Correct grammar in transcript: {asr_transcript} for file: {filename}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = correct_grammar_in_transcript(mock_client, "", "test_song.flac")

        # Check that empty string is returned
        self.assertEqual(result, "")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_correct_grammar_in_transcript_without_filename(self, mock_load_prompt, mock_openai_class):
        """Test grammatical correction without filename."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Correct grammar in transcript: {asr_transcript} for file: {filename}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "修正されたトランスクリプトです。"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        asr_transcript = "これはテストのトランスクリプトです"

        result = correct_grammar_in_transcript(mock_client, asr_transcript, None)

        # Check that correction was applied with None filename
        self.assertIsNotNone(result)
        self.assertEqual(result, "修正されたトランスクリプトです。")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_with_unicode_content(self, mock_load_prompt, mock_openai_class):
        """Test LRC generation with Unicode content."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}"

        # Mock OpenAI client and response with Unicode content
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        unicode_content = "[00:01.00]これはユニコードのテストです\n[00:05.00]特殊文字：あいうえお♪"
        mock_response.choices[0].message.content = unicode_content
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test data with Unicode
        lyrics_text = "これはユニコードのテストです"
        asr_transcript = "[0.92s -> 4.46s] これはユニコードのトランスクリプトです"

        result = generate_lrc_lyrics(mock_client, lyrics_text, asr_transcript)

        # Check that Unicode content was handled correctly
        self.assertIsNotNone(result)
        self.assertIn("ユニコード", result)
        self.assertIn("あいうえお♪", result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('generate_lrc.OpenAI')
    @patch('generate_lrc.load_prompt_template')
    def test_generate_lrc_lyrics_strips_response(self, mock_load_prompt, mock_openai_class):
        """Test that LRC generation strips whitespace from response."""
        # Mock prompt template loading
        mock_load_prompt.return_value = "Generate LRC from lyrics: {lyrics_text} and transcript: {lrc_transcript}"

        # Mock OpenAI client and response with extra whitespace
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  [00:01.00]テスト\n  [00:05.00]セカンドライン  \n"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = generate_lrc_lyrics(mock_client, "test lyrics", "test transcript")

        # Check that response was stripped
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("[00:01.00]"))
        self.assertFalse(result.startswith("  [00:01.00]"))


if __name__ == '__main__':
    unittest.main()