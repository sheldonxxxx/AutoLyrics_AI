#!/usr/bin/env python3
"""
Script to compare similarity between ASR content and downloaded lyrics.
Provides various similarity metrics to evaluate how well ASR transcription matches reference lyrics.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from difflib import SequenceMatcher, unified_diff
from collections import Counter
import unicodedata

from logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing punctuation, converting to lowercase,
    and normalizing unicode characters.

    Args:
        text (str): Text to normalize

    Returns:
        str: Normalized text
    """
    # Convert to lowercase
    text = text.lower()

    # Normalize unicode characters (e.g., full-width to half-width)
    text = unicodedata.normalize('NFKC', text)

    # Remove punctuation and special characters, but keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', '', text)

    # Normalize whitespace (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_text_from_transcript(transcript_content: str) -> str:
    """
    Extract actual transcribed text from ASR transcript, removing timestamps.

    Args:
        transcript_content (str): Raw transcript content with timestamps

    Returns:
        str: Clean text without timestamp information
    """
    # Remove timestamp lines like "Timestamped Transcription:" and "[5.48s -> 11.54s]"
    lines = transcript_content.split('\n')

    # Filter out header lines and extract text from timestamped lines
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('Timestamped Transcription:'):
            continue

        # Remove timestamp pattern [xx.xx -> yy.yy] from the beginning of lines
        # Also handle cases where timestamp might be in the middle or end
        line = re.sub(r'\[\d+\.\d+s\s*->\s*\d+\.\d+s\]\s*', '', line)
        line = re.sub(r'\[\d+\.\d+s\s*-\s*\d+\.\d+s\]\s*', '', line)

        if line.strip():
            text_lines.append(line.strip())

    return ' '.join(text_lines)


def remove_duplicate_lines(text: str) -> str:
    """
    Remove duplicate lines from text while preserving order.

    Args:
        text (str): Text that may contain duplicate lines

    Returns:
        str: Text with duplicate lines removed
    """
    lines = text.split('\n')
    seen = set()
    unique_lines = []

    for line in lines:
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            unique_lines.append(line)

    return '\n'.join(unique_lines)


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on word sets.

    Args:
        text1 (str): First text
        text2 (str): Second text

    Returns:
        float: Jaccard similarity score (0.0 to 1.0)
    """
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())

    if not words1 and not words2:
        return 1.0  # Both are empty

    if not words1 or not words2:
        return 0.0  # One is empty, other is not

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0


def calculate_sequence_similarity(text1: str, text2: str) -> float:
    """
    Calculate sequence similarity using SequenceMatcher.

    Args:
        text1 (str): First text
        text2 (str): Second text

    Returns:
        float: Sequence similarity score (0.0 to 1.0)
    """
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()


def calculate_levenshtein_similarity(text1: str, text2: str) -> float:
    """
    Calculate Levenshtein similarity (1 - normalized edit distance).

    Args:
        text1 (str): First text
        text2 (str): Second text

    Returns:
        float: Levenshtein similarity score (0.0 to 1.0)
    """
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)

    # Use SequenceMatcher for edit distance approximation
    matcher = SequenceMatcher(None, normalized1, normalized2)
    edit_distance = sum(
        (tag == 'delete' and (i2 - i1)) +
        (tag == 'insert' and (j2 - j1)) +
        (tag == 'replace' and max(i2 - i1, j2 - j1))
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
    )

    max_length = max(len(normalized1), len(normalized2))
    return 1.0 - (edit_distance / max_length) if max_length > 0 else 1.0


def find_common_phrases(text1: str, text2: str, min_length: int = 3) -> List[Tuple[str, int, int]]:
    """
    Find common phrases between two texts.

    Args:
        text1 (str): First text
        text2 (str): Second text
        min_length (int): Minimum length of phrases to consider

    Returns:
        List[Tuple[str, int, int]]: List of (phrase, start_pos1, start_pos2) tuples
    """
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)

    words1 = normalized1.split()
    words2 = normalized2.split()

    common_phrases = []

    # Use SequenceMatcher to find matching blocks
    matcher = SequenceMatcher(None, words1, words2)

    for match in matcher.get_matching_blocks():
        if match.size >= min_length:
            phrase_words = words1[match.a:match.a + match.size]
            phrase = ' '.join(phrase_words)
            common_phrases.append((phrase, match.a, match.b))

    return common_phrases


def calculate_word_overlap(text1: str, text2: str) -> Dict[str, float]:
    """
    Calculate detailed word overlap statistics.

    Args:
        text1 (str): First text
        text2 (str): Second text

    Returns:
        Dict[str, float]: Dictionary with overlap statistics
    """
    words1 = Counter(normalize_text(text1).split())
    words2 = Counter(normalize_text(text2).split())

    all_words = set(words1.keys()).union(set(words2.keys()))

    total_words1 = sum(words1.values())
    total_words2 = sum(words2.values())

    # Calculate various overlap metrics
    common_words = sum((words1 & words2).values())
    only_in_1 = sum((words1 - words2).values())
    only_in_2 = sum((words2 - words1).values())

    return {
        'common_words': common_words,
        'unique_to_text1': only_in_1,
        'unique_to_text2': only_in_2,
        'total_words_text1': total_words1,
        'total_words_text2': total_words2,
        'overlap_ratio_text1': common_words / total_words1 if total_words1 > 0 else 0.0,
        'overlap_ratio_text2': common_words / total_words2 if total_words2 > 0 else 0.0,
        'jaccard_similarity': common_words / (only_in_1 + only_in_2 + common_words) if (only_in_1 + only_in_2 + common_words) > 0 else 0.0
    }


def compare_lyrics_similarity(asr_content: str, lyrics_content: str) -> Dict[str, Any]:
    """
    Compare ASR content with downloaded lyrics and return detailed similarity analysis.

    Args:
        asr_content (str): ASR transcript content
        lyrics_content (str): Downloaded lyrics content

    Returns:
        Dict[str, Any]: Dictionary containing similarity metrics and analysis
    """
    logger.info("Starting lyrics similarity comparison...")

    # Extract clean text from ASR transcript (remove timestamps)
    clean_asr_content = extract_text_from_transcript(asr_content)

    # Remove duplicate lines from ASR content for better comparison
    deduplicated_asr = remove_duplicate_lines(clean_asr_content)

    logger.info(f"ASR content length: {len(clean_asr_content)} chars")
    logger.info(f"ASR content (deduplicated): {len(deduplicated_asr)} chars")
    logger.info(f"Lyrics content length: {len(lyrics_content)} chars")

    # Basic similarity metrics (using deduplicated ASR)
    jaccard_sim = calculate_jaccard_similarity(deduplicated_asr, lyrics_content)
    sequence_sim = calculate_sequence_similarity(deduplicated_asr, lyrics_content)
    levenshtein_sim = calculate_levenshtein_similarity(deduplicated_asr, lyrics_content)

    # Word overlap analysis
    word_overlap = calculate_word_overlap(deduplicated_asr, lyrics_content)

    # Find common phrases
    common_phrases = find_common_phrases(deduplicated_asr, lyrics_content)

    # Generate diff for detailed comparison
    diff_lines = list(unified_diff(
        normalize_text(deduplicated_asr).split(),
        normalize_text(lyrics_content).split(),
        lineterm='',
        fromfile='ASR',
        tofile='Lyrics'
    ))

    # Calculate overall similarity score (weighted average)
    overall_similarity = (jaccard_sim * 0.3 + sequence_sim * 0.4 + levenshtein_sim * 0.3)

    result = {
        'overall_similarity': overall_similarity,
        'jaccard_similarity': jaccard_sim,
        'sequence_similarity': sequence_sim,
        'levenshtein_similarity': levenshtein_sim,
        'word_overlap': word_overlap,
        'common_phrases': common_phrases,
        'common_phrases_count': len(common_phrases),
        'diff_summary': '\n'.join(diff_lines[:20]),  # First 20 lines of diff
        'asr_word_count': len(normalize_text(deduplicated_asr).split()),
        'lyrics_word_count': len(normalize_text(lyrics_content).split()),
        'asr_content_preview': deduplicated_asr[:200] + '...' if len(deduplicated_asr) > 200 else deduplicated_asr,
        'lyrics_content_preview': lyrics_content[:200] + '...' if len(lyrics_content) > 200 else lyrics_content,
        'similarity_category': categorize_similarity(overall_similarity)
    }

    logger.info(f"Similarity comparison completed. Overall similarity: {overall_similarity:.3f} ({result['similarity_category']})")

    return result


def categorize_similarity(similarity_score: float) -> str:
    """
    Categorize similarity score into descriptive categories.

    Args:
        similarity_score (float): Similarity score between 0.0 and 1.0

    Returns:
        str: Similarity category
    """
    if similarity_score >= 0.8:
        return "Very High"
    elif similarity_score >= 0.6:
        return "High"
    elif similarity_score >= 0.4:
        return "Moderate"
    elif similarity_score >= 0.2:
        return "Low"
    else:
        return "Very Low"


def print_similarity_report(result: Dict[str, Any]) -> None:
    """
    Print a formatted similarity report.

    Args:
        result (Dict[str, any]): Similarity analysis result from compare_lyrics_similarity
    """
    print("\n" + "="*60)
    print("LYRICS SIMILARITY ANALYSIS REPORT")
    print("="*60)

    print(f"Overall Similarity: {result['overall_similarity']:.3f} ({result['similarity_category']})")
    print(f"Jaccard Similarity: {result['jaccard_similarity']:.3f}")
    print(f"Sequence Similarity: {result['sequence_similarity']:.3f}")
    print(f"Levenshtein Similarity: {result['levenshtein_similarity']:.3f}")

    print("\nWord Overlap Analysis:")
    overlap = result['word_overlap']
    print(f"  Common words: {overlap['common_words']}")
    print(f"  Unique to ASR: {overlap['unique_to_text1']}")
    print(f"  Unique to Lyrics: {overlap['unique_to_text2']}")
    print(f"  ASR overlap ratio: {overlap['overlap_ratio_text1']:.3f}")
    print(f"  Lyrics overlap ratio: {overlap['overlap_ratio_text2']:.3f}")

    print(f"\nCommon phrases found: {result['common_phrases_count']}")
    if result['common_phrases'][:3]:  # Show first 3 common phrases
        print("Top common phrases:")
        for phrase, pos1, pos2 in result['common_phrases'][:3]:
            print(f"  '{phrase}' (ASR pos: {pos1}, Lyrics pos: {pos2})")

    print("\nWord count comparison:")
    print(f"  ASR: {result['asr_word_count']} words")
    print(f"  Lyrics: {result['lyrics_word_count']} words")

    print("\nContent Preview:")
    print(f"  ASR: {result['asr_content_preview']}")
    print(f"  Lyrics: {result['lyrics_content_preview']}")

    print("\n" + "="*60)


def main():
    """
    Main function for command-line usage.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Compare similarity between ASR content and downloaded lyrics.')
    parser.add_argument('asr_file', nargs='?', help='Path to ASR transcript file')
    parser.add_argument('lyrics_file', nargs='?', help='Path to lyrics file')
    parser.add_argument('--asr-text', help='ASR text content (alternative to file)')
    parser.add_argument('--lyrics-text', help='Lyrics text content (alternative to file)')
    parser.add_argument('--output', '-o', help='Output report file path')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(level=log_level)

    # Get ASR content
    asr_content = None
    if args.asr_text:
        asr_content = args.asr_text
        logger.info("Using ASR text from command line")
    elif args.asr_file:
        if not args.asr_file or not os.path.exists(args.asr_file):
            logger.error(f"ASR file does not exist: {args.asr_file}")
            return
        try:
            with open(args.asr_file, 'r', encoding='utf-8') as f:
                asr_content = f.read()
            logger.info(f"Loaded ASR content from: {args.asr_file}")
        except Exception as e:
            logger.error(f"Error reading ASR file: {e}")
            return
    else:
        logger.error("No ASR content provided. Use --asr-file or --asr-text")
        return

    # Get lyrics content
    lyrics_content = None
    if args.lyrics_text:
        lyrics_content = args.lyrics_text
        logger.info("Using lyrics text from command line")
    elif args.lyrics_file:
        if not args.lyrics_file or not os.path.exists(args.lyrics_file):
            logger.error(f"Lyrics file does not exist: {args.lyrics_file}")
            return
        try:
            with open(args.lyrics_file, 'r', encoding='utf-8') as f:
                lyrics_content = f.read()
            logger.info(f"Loaded lyrics content from: {args.lyrics_file}")
        except Exception as e:
            logger.error(f"Error reading lyrics file: {e}")
            return
    else:
        logger.error("No lyrics content provided. Use --lyrics-file or --lyrics-text")
        return

    # Perform similarity comparison
    result = compare_lyrics_similarity(asr_content, lyrics_content)

    # Print report
    print_similarity_report(result)

    # Save report to file if requested
    if args.output:
        try:
            import json
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Similarity report saved to: {args.output}")
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")


if __name__ == "__main__":
    main()