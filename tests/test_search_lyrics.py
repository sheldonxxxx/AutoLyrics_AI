#!/usr/bin/env python3
"""
Comprehensive unit tests for search_lyrics.py module.
"""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_lyrics import search_uta_net


class TestSearchLyrics(unittest.TestCase):
    """Test cases for lyrics search functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('search_lyrics.requests.get')
    @patch('search_lyrics.BeautifulSoup')
    def test_search_uta_net_success_with_title_search(self, mock_bs_class, mock_get):
        """Test successful lyrics search using title search."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results page
        mock_search_soup = MagicMock()
        search_link = MagicMock()
        search_link.get_text.return_value = "Test Song Title by Test Artist"
        search_link['href'] = "/song/12345/"
        mock_search_soup.find_all.return_value = [search_link]
        mock_bs_class.return_value = mock_search_soup

        # Mock BeautifulSoup for song page
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()
        lyrics_div.get_text.return_value = "これが最初の行です\nこれが二番目の行です"
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that lyrics were found and returned
        self.assertIsNotNone(result)
        self.assertIn("これが最初の行です", result)
        self.assertIn("これが二番目の行です", result)

        # Check that both title search and song page fetch were called
        self.assertEqual(mock_get.call_count, 2)  # Once for search, once for song page

    @patch('search_lyrics.requests.get')
    @patch('search_lyrics.BeautifulSoup')
    def test_search_uta_net_success_with_artist_fallback(self, mock_bs_class, mock_get):
        """Test successful lyrics search using artist fallback."""
        # Mock empty title search results, then successful artist search
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        # First call (title search) returns no results
        mock_response.text = "<html><body>No results</body></html>"
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for empty search results
        mock_empty_soup = MagicMock()
        mock_empty_soup.find_all.return_value = []
        mock_bs_class.return_value = mock_empty_soup

        # Second call (artist search) returns results
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """

        # Mock BeautifulSoup for artist search results
        mock_artist_soup = MagicMock()
        artist_link = MagicMock()
        artist_link.get_text.return_value = "Test Song Title by Test Artist"
        artist_link['href'] = "/song/12345/"
        mock_artist_soup.find_all.return_value = [artist_link]
        mock_bs_class.return_value = mock_artist_soup

        # Mock BeautifulSoup for song page
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()
        lyrics_div.get_text.return_value = "アーティスト検索からの歌詞"
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that lyrics were found using artist fallback
        self.assertIsNotNone(result)
        self.assertIn("アーティスト検索からの歌詞", result)

        # Check that three HTTP calls were made (title search, artist search, song page)
        self.assertEqual(mock_get.call_count, 3)

    @patch('search_lyrics.requests.get')
    def test_search_uta_net_no_results_found(self, mock_get):
        """Test lyrics search when no results are found."""
        # Mock HTTP response with no results
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html><body>No song links found</body></html>"
        mock_get.return_value = mock_response

        # Mock BeautifulSoup that finds no links
        with patch('search_lyrics.BeautifulSoup') as mock_bs_class:
            mock_soup = MagicMock()
            mock_soup.find_all.return_value = []
            mock_bs_class.return_value = mock_soup

            result = search_uta_net("Nonexistent Song", "Nonexistent Artist")

            # Check that no lyrics were found
            self.assertIsNone(result)

    @patch('search_lyrics.requests.get')
    def test_search_uta_net_http_error(self, mock_get):
        """Test lyrics search with HTTP error."""
        # Mock HTTP error response
        mock_get.side_effect = Exception("Connection error")

        result = search_uta_net("Test Song", "Test Artist")

        # Check that no lyrics were returned due to error
        self.assertIsNone(result)

    @patch('search_lyrics.requests.get')
    @patch('search_lyrics.BeautifulSoup')
    def test_search_uta_net_lyrics_not_found_on_song_page(self, mock_bs_class, mock_get):
        """Test lyrics search when song page exists but lyrics not found."""
        # Mock successful search results
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results
        mock_search_soup = MagicMock()
        search_link = MagicMock()
        search_link.get_text.return_value = "Test Song Title by Test Artist"
        search_link['href'] = "/song/12345/"
        mock_search_soup.find_all.return_value = [search_link]
        mock_bs_class.return_value = mock_search_soup

        # Mock song page without lyrics
        mock_song_soup = MagicMock()
        mock_song_soup.find.return_value = None  # No lyrics div found
        mock_song_soup.find_all.return_value = []  # No alternative lyrics divs
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that no lyrics were found
        self.assertIsNone(result)

    @patch('search_uta_net.requests.get')
    @patch('search_uta_net.BeautifulSoup')
    def test_search_uta_net_lyrics_with_br_tags(self, mock_bs_class, mock_get):
        """Test lyrics extraction when lyrics contain <br> tags."""
        # Mock successful search results
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results
        mock_search_soup = MagicMock()
        search_link = MagicMock()
        search_link.get_text.return_value = "Test Song Title by Test Artist"
        search_link['href'] = "/song/12345/"
        mock_search_soup.find_all.return_value = [search_link]
        mock_bs_class.return_value = mock_search_soup

        # Mock song page with lyrics containing <br> tags
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()

        # Create mock elements to simulate lyrics with line breaks
        br_element = MagicMock()
        br_element.name = 'br'

        text_element1 = MagicMock()
        text_element1.name = None  # String element
        text_element1.strip.return_value = "これが最初の行です"

        text_element2 = MagicMock()
        text_element2.name = None  # String element
        text_element2.strip.return_value = "これが二番目の行です"

        lyrics_div.descendants = [text_element1, br_element, text_element2]
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that lyrics were extracted with line breaks
        self.assertIsNotNone(result)
        self.assertIn("これが最初の行です", result)
        self.assertIn("これが二番目の行です", result)

    @patch('search_uta_net.requests.get')
    @patch('search_uta_net.BeautifulSoup')
    def test_search_uta_net_first_result_fallback(self, mock_bs_class, mock_get):
        """Test fallback to first search result when specific song not found."""
        # Mock search results that don't match our song exactly
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/999/">Different Song by Different Artist</a>
                <a href="/song/12345/">Another Song by Another Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results
        mock_search_soup = MagicMock()
        search_links = []

        # Create links that don't match our target song
        for i, (title, artist) in enumerate([
            ("Different Song", "Different Artist"),
            ("Another Song", "Another Artist")
        ]):
            link = MagicMock()
            link.get_text.return_value = f"{title} by {artist}"
            link['href'] = f"/song/{i}/"
            search_links.append(link)

        mock_search_soup.find_all.return_value = search_links
        mock_bs_class.return_value = mock_search_soup

        # Mock song page for first result
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()
        lyrics_div.get_text.return_value = "最初の検索結果からの歌詞"
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that first result was used as fallback
        self.assertIsNotNone(result)
        self.assertIn("最初の検索結果からの歌詞", result)

    @patch('search_uta_net.requests.get')
    def test_search_uta_net_request_exception(self, mock_get):
        """Test lyrics search with requests exception."""
        # Mock various request exceptions
        mock_get.side_effect = Exception("Request failed")

        result = search_uta_net("Test Song", "Test Artist")

        # Check that no lyrics were returned due to exception
        self.assertIsNone(result)

    @patch('search_uta_net.requests.get')
    @patch('search_uta_net.BeautifulSoup')
    def test_search_uta_net_empty_lyrics_text(self, mock_bs_class, mock_get):
        """Test lyrics search when lyrics text is empty."""
        # Mock successful search results
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results
        mock_search_soup = MagicMock()
        search_link = MagicMock()
        search_link.get_text.return_value = "Test Song Title by Test Artist"
        search_link['href'] = "/song/12345/"
        mock_search_soup.find_all.return_value = [search_link]
        mock_bs_class.return_value = mock_search_soup

        # Mock song page with empty lyrics
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()
        lyrics_div.get_text.return_value = ""  # Empty lyrics
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that no lyrics were returned due to empty content
        self.assertIsNone(result)

    @patch('search_uta_net.requests.get')
    @patch('search_uta_net.BeautifulSoup')
    def test_search_uta_net_lyrics_with_formatting_cleanup(self, mock_bs_class, mock_get):
        """Test lyrics search with text formatting cleanup."""
        # Mock successful search results
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        <html>
            <body>
                <a href="/song/12345/">Test Song Title by Test Artist</a>
            </body>
        </html>
        """
        mock_get.return_value = mock_response

        # Mock BeautifulSoup for search results
        mock_search_soup = MagicMock()
        search_link = MagicMock()
        search_link.get_text.return_value = "Test Song Title by Test Artist"
        search_link['href'] = "/song/12345/"
        mock_search_soup.find_all.return_value = [search_link]
        mock_bs_class.return_value = mock_search_soup

        # Mock song page with messy lyrics formatting
        mock_song_soup = MagicMock()
        lyrics_div = MagicMock()
        # Simulate the get_text() method that cleans up formatting
        messy_lyrics = "  これが最初の行です  \n\n\n  これが二番目の行です  \n  これが三番目の行です  "
        lyrics_div.get_text.return_value = messy_lyrics
        mock_song_soup.find.return_value = lyrics_div
        mock_bs_class.return_value = mock_song_soup

        result = search_uta_net("Test Song Title", "Test Artist")

        # Check that lyrics were cleaned up properly
        self.assertIsNotNone(result)
        # The actual cleanup happens in the function's text processing
        self.assertTrue(len(result.strip()) > 0)


if __name__ == '__main__':
    unittest.main()