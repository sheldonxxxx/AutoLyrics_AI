#!/usr/bin/env python3
"""
Test script to verify that get_output_paths preserves nested folder structure.
"""

import sys
from pathlib import Path
from utils import get_output_paths

def test_folder_structure_preservation():
    """Test that nested folder structure is preserved in output paths."""

    # Create test scenarios
    test_cases = [
        # (input_file, input_base_dir, expected_nested_structure)
        (
            Path("input/artist/album/song.flac"),
            "input",
            "artist/album"
        ),
        (
            Path("input/various/song.flac"),
            "input",
            "various"
        ),
        (
            Path("input/song.flac"),
            "input",
            ""  # No nested structure
        ),
        (
            Path("music/jpop/artist/album/song.flac"),
            "music",
            "jpop/artist/album"
        )
    ]

    print("Testing folder structure preservation in get_output_paths...")
    print("=" * 60)

    for i, (input_file, input_base_dir, expected_structure) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input file: {input_file}")
        print(f"Input base dir: {input_base_dir}")
        print(f"Expected nested structure: '{expected_structure}'")

        try:
            paths = get_output_paths(input_file, "output", "tmp", input_base_dir)

            # Check if nested structure is preserved
            temp_vocals_path = paths['vocals_wav']
            output_lrc_path = paths['translated_lrc']

            print(f"Temp vocals path: {temp_vocals_path}")
            print(f"Output LRC path: {output_lrc_path}")

            # Simple check: verify that both paths contain the expected nested structure
            temp_str = str(temp_vocals_path)
            output_str = str(output_lrc_path)

            # Check if the expected nested structure appears in both paths
            temp_has_structure = expected_structure in temp_str
            output_has_structure = expected_structure in output_str

            print(f"Temp path contains '{expected_structure}': {temp_has_structure}")
            print(f"Output path contains '{expected_structure}': {output_has_structure}")

            # Check if both temp and output have the same nested structure
            if temp_has_structure and output_has_structure:
                print("✅ PASS: Nested structure preserved correctly")
            else:
                print("❌ FAIL: Nested structure not preserved correctly")
                print(f"Expected nested structure '{expected_structure}' not found in both paths")
                return False

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! Folder structure preservation is working correctly.")
    return True

if __name__ == "__main__":
    success = test_folder_structure_preservation()
    sys.exit(0 if success else 1)