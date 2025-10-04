#!/usr/bin/env python3
"""
Comprehensive unit tests for extract_metadata.py module.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract_metadata import extract_metadata


class TestExtractMetadata(unittest.TestCase):
    """Test cases for metadata extraction functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create mock audio files for testing
        self.flac_file = os.path.join(self.temp_dir, "test.flac")
        self.mp3_file = os.path.join(self.temp_dir, "test.mp3")
        self.wav_file = os.path.join(self.temp_dir, "test.wav")

        # Create empty files (they won't have real metadata but we can test file handling)
        with open(self.flac_file, 'wb') as f:
            f.write(b'fake flac content')
        with open(self.mp3_file, 'wb') as f:
            f.write(b'fake mp3 content')
        with open(self.wav_file, 'wb') as f:
            f.write(b'fake wav content')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('extract_metadata.File')
    @patch('extract_metadata.FLAC')
    def test_extract_metadata_from_flac_with_tags(self, mock_flac_class, mock_file_class):
        """Test metadata extraction from FLAC file with tags."""
        # Mock FLAC file with metadata
        mock_flac = MagicMock()
        mock_flac.tags = {
            'TITLE': ['Test Song Title'],
            'ARTIST': ['Test Artist'],
            'ALBUM': ['Test Album'],
            'GENRE': ['Pop'],
            'DATE': ['2023'],
            'TRACKNUMBER': ['5']
        }
        mock_flac_class.return_value = mock_flac

        result = extract_metadata(self.flac_file)

        # Check that metadata was extracted correctly
        self.assertEqual(result['title'], 'Test Song Title')
        self.assertEqual(result['artist'], 'Test Artist')
        self.assertEqual(result['album'], 'Test Album')
        self.assertEqual(result['genre'], 'Pop')
        self.assertEqual(result['year'], '2023')
        self.assertEqual(result['track_number'], '5')

    @patch('extract_metadata.File')
    def test_extract_metadata_from_mp3_with_tags(self, mock_file_class):
        """Test metadata extraction from MP3 file with tags."""
        # Mock MP3 file with metadata
        mock_file = MagicMock()
        mock_file.tags = {
            'TIT2': ['MP3 Song Title'],  # Title tag for MP3
            'TPE1': ['MP3 Artist'],     # Artist tag for MP3
            'TALB': ['MP3 Album'],      # Album tag for MP3
            'TCON': ['Rock'],           # Genre tag for MP3
            'TYER': ['2022'],           # Year tag for MP3
            'TRCK': ['3']               # Track tag for MP3
        }
        mock_file_class.return_value = mock_file

        result = extract_metadata(self.mp3_file)

        # Check that metadata was extracted correctly
        self.assertEqual(result['title'], 'MP3 Song Title')
        self.assertEqual(result['artist'], 'MP3 Artist')
        self.assertEqual(result['album'], 'MP3 Album')
        self.assertEqual(result['genre'], 'Rock')
        self.assertEqual(result['year'], '2022')
        self.assertEqual(result['track_number'], '3')

    @patch('extract_metadata.File')
    def test_extract_metadata_from_file_without_tags(self, mock_file_class):
        """Test metadata extraction from file without tags (filename fallback)."""
        # Mock file without tags
        mock_file = MagicMock()
        mock_file.tags = None
        mock_file_class.return_value = mock_file

        # Test with filename containing "Artist - Title"
        artist_title_file = os.path.join(self.temp_dir, "Test Artist - Test Title.flac")
        with open(artist_title_file, 'wb') as f:
            f.write(b'fake content')

        result = extract_metadata(artist_title_file)

        # Check that metadata was extracted from filename
        self.assertEqual(result['artist'], 'Test Artist')
        self.assertEqual(result['title'], 'Test Title')

    @patch('extract_metadata.File')
    def test_extract_metadata_from_file_without_tags_no_dash(self, mock_file_class):
        """Test metadata extraction from file without tags and no dash in filename."""
        # Mock file without tags
        mock_file = MagicMock()
        mock_file.tags = None
        mock_file_class.return_value = mock_file

        # Test with filename without " - " separator
        no_dash_file = os.path.join(self.temp_dir, "JustTitle.flac")
        with open(no_dash_file, 'wb') as f:
            f.write(b'fake content')

        result = extract_metadata(no_dash_file)

        # Check that only title is extracted
        self.assertEqual(result['title'], 'JustTitle')
        self.assertIsNone(result['artist'])

    @patch('extract_metadata.File')
    def test_extract_metadata_with_list_values(self, mock_file_class):
        """Test metadata extraction when tag values are lists."""
        # Mock file with list values for tags
        mock_file = MagicMock()
        mock_file.tags = {
            'TITLE': ['Song Title'],  # List with one item
            'ARTIST': ['Artist 1', 'Artist 2'],  # List with multiple items
            'ALBUM': 'Single Album'  # Single value (not a list)
        }
        mock_file_class.return_value = mock_file

        result = extract_metadata(self.flac_file)

        # Check that first item from list is used
        self.assertEqual(result['title'], 'Song Title')
        self.assertEqual(result['artist'], 'Artist 1')  # First artist from list
        self.assertEqual(result['album'], 'Single Album')

    @patch('extract_metadata.File')
    def test_extract_metadata_priority_order(self, mock_file_class):
        """Test that metadata extraction follows priority order."""
        # Mock file with multiple possible title tags
        mock_file = MagicMock()
        mock_file.tags = {
            'TITLE': ['Low Priority Title'],      # Should be overridden
            'TRACKTITLE': ['High Priority Title'], # Higher priority
            'ARTIST': ['Low Priority Artist'],     # Should be overridden
            'TPE1': ['High Priority Artist'],      # Higher priority (MP3 format)
        }
        mock_file_class.return_value = mock_file

        result = extract_metadata(self.mp3_file)

        # Check that higher priority tags are used
        self.assertEqual(result['title'], 'High Priority Title')
        self.assertEqual(result['artist'], 'High Priority Artist')

    @patch('extract_metadata.File')
    def test_extract_metadata_with_id3_no_header_error(self, mock_file_class):
        """Test metadata extraction with ID3 no header error."""
        from mutagen.id3 import ID3NoHeaderError

        # Mock file that raises ID3NoHeaderError
        mock_file_class.side_effect = ID3NoHeaderError("No ID3 header")

        result = extract_metadata(self.mp3_file)

        # Should return empty metadata dict
        self.assertIsNone(result['title'])
        self.assertIsNone(result['artist'])
        self.assertIsNone(result['album'])
        self.assertIsNone(result['genre'])
        self.assertIsNone(result['year'])
        self.assertIsNone(result['track_number'])

    @patch('extract_metadata.FLAC')
    def test_extract_metadata_with_flac_no_header_error(self, mock_flac_class):
        """Test metadata extraction with FLAC no header error."""
        from mutagen.flac import FLACNoHeaderError

        # Mock FLAC file that raises FLACNoHeaderError
        mock_flac_class.side_effect = FLACNoHeaderError("No FLAC header")

        result = extract_metadata(self.flac_file)

        # Should return empty metadata dict
        self.assertIsNone(result['title'])
        self.assertIsNone(result['artist'])
        self.assertIsNone(result['album'])
        self.assertIsNone(result['genre'])
        self.assertIsNone(result['year'])
        self.assertIsNone(result['track_number'])

    @patch('extract_metadata.File')
    def test_extract_metadata_with_general_exception(self, mock_file_class):
        """Test metadata extraction with general exception."""
        # Mock file that raises a general exception
        mock_file_class.side_effect = Exception("General error")

        result = extract_metadata(self.flac_file)

        # Should return empty metadata dict
        self.assertIsNone(result['title'])
        self.assertIsNone(result['artist'])
        self.assertIsNone(result['album'])
        self.assertIsNone(result['genre'])
        self.assertIsNone(result['year'])
        self.assertIsNone(result['track_number'])

    @patch('extract_metadata.File')
    def test_extract_metadata_with_whitespace_only_values(self, mock_file_class):
        """Test metadata extraction with whitespace-only values."""
        # Mock file with whitespace-only tag values
        mock_file = MagicMock()
        mock_file.tags = {
            'TITLE': ['   '],  # Whitespace only
            'ARTIST': [''],    # Empty string
            'ALBUM': ['Valid Album']  # Valid value
        }
        mock_file_class.return_value = mock_file

        result = extract_metadata(self.flac_file)

        # Should skip whitespace-only and empty values
        self.assertIsNone(result['title'])
        self.assertIsNone(result['artist'])
        self.assertEqual(result['album'], 'Valid Album')

    @patch('extract_metadata.File')
    def test_extract_metadata_comprehensive_tag_coverage(self, mock_file_class):
        """Test metadata extraction with comprehensive tag coverage."""
        # Mock file with various tag formats
        mock_file = MagicMock()
        mock_file.tags = {
            # Title tags (various formats)
            'title': ['Standard Title'],
            '©nam': ['iTunes Title'],  # iTunes format

            # Artist tags (various formats)
            'artist': ['Standard Artist'],
            '©art': ['iTunes Artist'],  # iTunes format

            # Album tags
            'album': ['Standard Album'],
            '©alb': ['iTunes Album'],

            # Genre tags
            'genre': ['Standard Genre'],
            '©gen': ['iTunes Genre'],

            # Year/Date tags
            'date': ['2023'],
            'year': ['2022'],  # This should be overridden by date (lower priority number)
            '©day': ['iTunes Date'],

            # Track number tags
            'tracknumber': ['5'],
            'track': ['3'],  # This should be overridden by tracknumber
            '©trk': ['iTunes Track'],
        }
        mock_file_class.return_value = mock_file

        result = extract_metadata(self.flac_file)

        # Check that the highest priority tags are used
        self.assertEqual(result['title'], 'Standard Title')  # Standard title has priority
        self.assertEqual(result['artist'], 'Standard Artist')  # Standard artist has priority
        self.assertEqual(result['album'], 'Standard Album')  # Standard album has priority
        self.assertEqual(result['genre'], 'Standard Genre')  # Standard genre has priority
        self.assertEqual(result['year'], '2023')  # date has higher priority than year
        self.assertEqual(result['track_number'], '5')  # tracknumber has higher priority than track


if __name__ == '__main__':
    unittest.main()