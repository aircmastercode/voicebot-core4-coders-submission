import asyncio
import logging
import os
from typing import AsyncGenerator, Callable, Optional

from dotenv import load_dotenv
import yaml
from pathlib import Path

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ASRConfig:
    """Configuration for the ASR module, loaded from config.yaml."""
    def __init__(self, languages: list = None):
        self.languages = languages or ["en", "hi"]  # Default to English and Hindi

    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "ASRConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            asr_config = config.get("asr", {})
            return cls(
                languages=asr_config.get("languages", ["en", "hi"])
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class ASRModule:
    """
    Handles Speech-to-Text (ASR) conversion (frontend implementation).
    This is now a mock implementation since speech recognition is handled in the frontend.
    """
    def __init__(self, config: ASRConfig):
        self.config = config

        logger.info(f"ASR Module initialized successfully. Languages: {', '.join(self.config.languages)}")

    async def stream_speech_to_text(self, audio_stream: AsyncGenerator[bytes, None], on_transcription: Callable[[str], None]):
        """
        Mock implementation since speech recognition is now handled in the frontend.
        Args:
            audio_stream: An async generator yielding audio chunks (bytes).
            on_transcription: A callback function to be called with each transcription update.
        """
        logger.info("ASR is now handled in the frontend. This is a mock implementation.")
        # Just consume the audio stream to avoid hanging
        full_audio_data = b''
        async for chunk in audio_stream:
            full_audio_data += chunk

        # Call the callback with an empty string or a message
        on_transcription("Speech recognition is now handled in the frontend.")
        
    def transcribe_file(self, file_path: str) -> str:
        """
        Mock implementation for transcribing an audio file to text.
        Args:
            file_path: Path to the audio file.
        Returns:
            A message indicating that transcription is now handled in the frontend.
        """
        logger.info(f"Mock transcription for file: {file_path}")
        return "Speech recognition is now handled in the frontend."

# Example Usage
async def main():
    logging.basicConfig(level=logging.INFO)

    # Mock audio stream for demonstration
    async def mock_audio_stream():
        # In a real application, this would come from a microphone or audio file
        for _ in range(5):
            yield b"" # Empty bytes for demonstration, replace with actual audio data
            await asyncio.sleep(0.5)

    def handle_transcription(transcript: str):
        print(f"Received transcription: {transcript}")

    try:
        asr_config = ASRConfig.from_yaml()
        asr = ASRModule(config=asr_config)

        print("Starting STT stream...")
        await asr.stream_speech_to_text(mock_audio_stream(), handle_transcription)
        print("STT stream finished.")

    except Exception as e:
        logger.error(f"Error in ASR module example: {e}")

if __name__ == '__main__':
    asyncio.run(main())