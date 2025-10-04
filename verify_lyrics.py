#!/usr/bin/env python3
"""
Script to verify if downloaded lyrics match ASR transcript content using LLM.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from logging_config import get_logger
from utils import get_openai_config, load_prompt_template

logger = get_logger(__name__)


class LyricsVerification(BaseModel):
    """Structured output for lyrics verification results."""
    match: bool = Field(description="Whether the lyrics match the ASR transcript")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Explanation of the verification decision")
    similarity_score: float = Field(description="Similarity score between 0.0 and 1.0")
    key_matches: list[str] = Field(description="List of matching elements found")
    discrepancies: list[str] = Field(description="List of major differences identified")


class LyricsVerifier:
    """Class to verify if downloaded lyrics match ASR transcript content."""

    def __init__(self):
        """Initialize the lyrics verifier with LLM."""
        load_dotenv()

        # Get OpenAI configuration using utility function
        config = get_openai_config()

        # Create OpenAI provider with custom configuration
        openai_provider = OpenAIProvider(
            base_url=config["OPENAI_BASE_URL"],
            api_key=config["OPENAI_API_KEY"]
        )

        # Create OpenAI model with the provider
        openai_model = OpenAIChatModel(
            config["OPENAI_MODEL"],
            provider=openai_provider
        )

        # Create Pydantic AI agent with the model
        self.agent = Agent(
            openai_model,
            output_type=LyricsVerification
        )

    def verify_lyrics_match(self, lyrics_text: str, asr_transcript: str) -> Optional[LyricsVerification]:
        """
        Verify if downloaded lyrics match ASR transcript content.

        Args:
            lyrics_text (str): Downloaded lyrics text
            asr_transcript (str): ASR transcript content

        Returns:
            Optional[LyricsVerification]: Verification result or None if verification fails
        """
        if not lyrics_text or not lyrics_text.strip():
            logger.error("Empty or invalid lyrics text provided")
            return None

        if not asr_transcript or not asr_transcript.strip():
            logger.error("Empty or invalid ASR transcript provided")
            return None

        try:
            # Load prompt template from file
            prompt_template_path = os.path.join(
                os.path.dirname(__file__),
                "prompt",
                "lyrics_verification_prompt.txt"
            )
            prompt_template = load_prompt_template(prompt_template_path)

            if not prompt_template:
                logger.error("Failed to load lyrics verification prompt template")
                return None

            # Format the prompt with actual data
            user_prompt = prompt_template.format(
                lyrics_text=lyrics_text.strip()[:4000],  # Limit input size
                asr_transcript=asr_transcript.strip()[:4000]  # Limit input size
            )

            # Use Pydantic AI agent to run the verification
            logger.info("Running lyrics verification with LLM")
            result = self.agent.run_sync(user_prompt)

            # Validate the result
            if not result or not result.output:
                logger.error("No result returned from lyrics verification")
                return None

            if not isinstance(result.output, LyricsVerification):
                logger.error(f"Invalid result type: {type(result.output)}")
                return None

            verification_result = result.output

            # Validate required fields
            if not verification_result.reasoning:
                logger.warning("Missing reasoning in verification result")
                return None

            # Validate confidence and similarity scores
            if not (0.0 <= verification_result.confidence <= 1.0):
                logger.warning(f"Invalid confidence score: {verification_result.confidence}")
                return None

            if not (0.0 <= verification_result.similarity_score <= 1.0):
                logger.warning(f"Invalid similarity score: {verification_result.similarity_score}")
                return None

            logger.info(
                f"Lyrics verification completed: match={verification_result.match}, "
                f"confidence={verification_result.confidence:.2f}, "
                f"similarity={verification_result.similarity_score:.2f}"
            )

            return verification_result

        except Exception as e:
            logger.error(f"Error during lyrics verification: {e}", exc_info=True)
            return None


def verify_lyrics_match(lyrics_text: str, asr_transcript: str) -> Tuple[bool, float, str]:
    """
    Convenience function to verify if lyrics match ASR transcript.

    Args:
        lyrics_text (str): Downloaded lyrics text
        asr_transcript (str): ASR transcript content

    Returns:
        Tuple[bool, float, str]: (is_match, confidence_score, reasoning)
    """
    verifier = LyricsVerifier()
    result = verifier.verify_lyrics_match(lyrics_text, asr_transcript)

    if result:
        return result.match, result.confidence, result.reasoning
    else:
        logger.warning("Lyrics verification failed, assuming no match")
        return False, 0.0, "Verification failed"


def main():
    """Test function for lyrics verification."""
    import argparse

    parser = argparse.ArgumentParser(description='Verify if downloaded lyrics match ASR transcript')
    parser.add_argument('--lyrics', '-l', help='Lyrics text or file path')
    parser.add_argument('--transcript', '-t', help='ASR transcript text or file path')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)

    # Get lyrics content
    lyrics_text = args.lyrics
    if not lyrics_text:
        print("No lyrics provided. Use --lyrics")
        return 1

    # Check if lyrics is a file path
    if os.path.exists(lyrics_text):
        try:
            with open(lyrics_text, 'r', encoding='utf-8') as f:
                lyrics_text = f.read()
        except Exception as e:
            print(f"Error reading lyrics file: {e}")
            return 1

    # Get transcript content
    transcript_text = args.transcript
    if not transcript_text:
        print("No transcript provided. Use --transcript")
        return 1

    # Check if transcript is a file path
    if os.path.exists(transcript_text):
        try:
            with open(transcript_text, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
        except Exception as e:
            print(f"Error reading transcript file: {e}")
            return 1

    print("Verifying lyrics match...")
    is_match, confidence, reasoning = verify_lyrics_match(lyrics_text, transcript_text)

    print(f"Match: {is_match}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Reasoning: {reasoning}")

    return 0 if is_match else 1


if __name__ == "__main__":
    exit(main())