#!/usr/bin/env python3
"""
Test script for extract_web_content function in utils.py.

This script reads test.txt and tests the extract_web_content function
to demonstrate its ability to clean web content by removing markdown,
HTML, links, and other web artifacts.
"""

import sys
from pathlib import Path

# Add the current directory to Python path to import utils
sys.path.append(str(Path(__file__).parent))

from utils import extract_web_content


def main():
    """Main function to test extract_web_content with test.txt."""

    # Read test.txt file
    test_file = Path("test.txt")

    if not test_file.exists():
        print(f"Error: {test_file} not found!")
        return False

    print("Reading test.txt...")
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading test.txt: {e}")
        return False


    # Test the extract_web_content function
    print("Testing extract_web_content function...")
    try:
        cleaned_content = extract_web_content(original_content)
    except Exception as e:
        print(f"Error in extract_web_content: {e}")
        return False

    # Save cleaned content to file for inspection
    output_file = Path("test_cleaned_output.txt")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"\nCleaned content saved to: {output_file}")
    except Exception as e:
        print(f"Error saving cleaned content: {e}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)