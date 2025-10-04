#!/usr/bin/env python3
"""
Comprehensive unit tests for translate_lrc.py module.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translate_lrc import translate_lrc_content


class TestTranslateLRC(unittest.TestCase):
    """Test cases for LRC translation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test LRC content
        self.test_lrc_content = """[ti:Test Song]
[ar:Test Artist]
[00:01.00]これは最初の行です
[00:05.00]これは二番目の行です
[00:10.00]これは三番目の行です"""

        # Create test prompt file
        self.prompt_file = os.path.join(self.temp_dir, "lrc_traditional_chinese_prompt.txt")
        with open(self.prompt_file, 'w', encoding='utf-8') as f:
            f.write("Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'TRANSLATION_MODEL': 'test_translation_model'
    })
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_success(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test successful LRC content translation."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        translated_content = """[ti:Test Song]
[ar:Test Artist]
[00:01.00]這是第一行
[00:05.00]這是第二行
[00:10.00]這是第三行"""
        mock_response.choices[0].message.content = translated_content
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that translation was successful
        self.assertIsNotNone(result)
        self.assertIn("[00:01.00]這是第一行", result)
        self.assertIn("[00:05.00]這是第二行", result)
        self.assertIn("[00:10.00]這是第三行", result)
        self.assertIn("[ti:Test Song]", result)  # Metadata should be preserved
        self.assertIn("[ar:Test Artist]", result)

        # Check that API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'test_translation_model')
        self.assertEqual(call_args[1]['temperature'], 0.1)
        self.assertEqual(call_args[1]['max_tokens'], 4000)

    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'OPENAI_MODEL': 'test_model'  # No TRANSLATION_MODEL set
    })
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_fallback_model(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation with fallback model."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[00:01.00]翻譯結果"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that fallback model was used
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'test_model')  # Should use OPENAI_MODEL as fallback

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_unsupported_language(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation with unsupported language."""
        # Mock prompt file selection to return empty string (unsupported language)
        mock_get_prompt_file.return_value = ""

        result = translate_lrc_content(mock_client, self.test_lrc_content, "English")

        # Check that None is returned for unsupported language
        self.assertIsNone(result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_prompt_template_not_found(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation when prompt template is not found."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading to return None
        mock_load_prompt.return_value = None

        mock_client = MagicMock()

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that None is returned when prompt template not found
        self.assertIsNone(result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_api_exception(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation with API exception."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that None is returned on API exception
        self.assertIsNone(result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_preserves_timestamps(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test that LRC translation preserves timestamps."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Response with same timestamps but translated text
        translated_content = """[ti:測試歌曲]
[ar:測試藝人]
[00:01.00]這是第一行
[00:05.00]這是第二行
[00:10.00]這是第三行"""
        mock_response.choices[0].message.content = translated_content
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that timestamps are preserved
        self.assertIsNotNone(result)
        self.assertIn("[00:01.00]", result)
        self.assertIn("[00:05.00]", result)
        self.assertIn("[00:10.00]", result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_preserves_metadata(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test that LRC translation preserves metadata lines."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Response with translated metadata
        translated_content = """[ti:測試歌曲]
[ar:測試藝人]
[al:測試專輯]
[00:01.00]這是第一行"""
        mock_response.choices[0].message.content = translated_content
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that metadata lines are preserved (and can be translated)
        self.assertIsNotNone(result)
        self.assertIn("[ti:", result)
        self.assertIn("[ar:", result)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_strips_response(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test that LRC translation strips whitespace from response."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response with extra whitespace
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  [00:01.00]翻譯結果  \n  [00:05.00]第二行  \n"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, self.test_lrc_content, "Traditional Chinese")

        # Check that response was stripped
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("[00:01.00]"))
        self.assertFalse(result.startswith("  [00:01.00]"))

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_empty_content(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation with empty content."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        result = translate_lrc_content(mock_client, "", "Traditional Chinese")

        # Check that empty string is returned
        self.assertEqual(result, "")

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('translate_lrc.OpenAI')
    @patch('translate_lrc.load_prompt_template')
    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_with_unicode(self, mock_get_prompt_file, mock_load_prompt, mock_openai_class):
        """Test LRC translation with Unicode content."""
        # Mock prompt file selection
        mock_get_prompt_file.return_value = "lrc_traditional_chinese_prompt.txt"

        # Mock prompt template loading
        mock_load_prompt.return_value = "Translate LRC to Traditional Chinese: {target_language}\nContent: {lrc_content}"

        # Mock OpenAI client and response with Unicode
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        unicode_content = "[00:01.00]這是繁體中文翻譯♪\n[00:05.00]包含特殊字符：あいうえお"
        mock_response.choices[0].message.content = unicode_content
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test with Unicode content
        unicode_lrc = "[00:01.00]これはテストです♪\n[00:05.00]これは日本語です"
        result = translate_lrc_content(mock_client, unicode_lrc, "Traditional Chinese")

        # Check that Unicode content was handled correctly
        self.assertIsNotNone(result)
        self.assertIn("繁體中文", result)
        self.assertIn("♪", result)  # Special characters should be preserved

    @patch('translate_lrc.get_prompt_file_for_language')
    def test_translate_lrc_content_unsupported_language_check(self, mock_get_prompt_file):
        """Test that unsupported languages are properly handled."""
        # Mock prompt file selection to return empty string
        mock_get_prompt_file.return_value = ""

        mock_client = MagicMock()

        result = translate_lrc_content(mock_client, self.test_lrc_content, "English")

        # Check that None is returned for unsupported language
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()