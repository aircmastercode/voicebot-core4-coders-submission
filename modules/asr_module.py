import asyncio
import logging
import os
from typing import AsyncGenerator, Callable, Optional

from dotenv import load_dotenv
import yaml
import requests
from pathlib import Path

from modules.eleven_ws import ElevenLabsWebSocketClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ASRConfig:
    """Configuration for the ASR module, loaded from config.yaml."""
    def __init__(self, model_id: str = "scribe_v1", languages: list = None): # ElevenLabs STT model
        self.model_id = model_id
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.languages = languages or ["en", "hi"]  # Default to English and Hindi

    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "ASRConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            asr_config = config.get("asr", {})
            return cls(
                model_id=asr_config.get("model_id", "scribe_v1"),
                languages=asr_config.get("languages", ["en", "hi"])
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class ASRModule:
    """
    Handles Speech-to-Text (ASR) conversion using ElevenLabs streaming API.
    """
    def __init__(self, config: ASRConfig):
        self.config = config
        self.elevenlabs_client = ElevenLabsWebSocketClient(
            api_key=self.config.elevenlabs_api_key,
            model_id=self.config.model_id
        )
        # Set supported languages
        self.elevenlabs_client.supported_languages = self.config.languages
        logger.info(f"ASR Module initialized successfully with ElevenLabs. Languages: {', '.join(self.config.languages)}")

    async def stream_speech_to_text(self, audio_stream: AsyncGenerator[bytes, None], on_transcription: Callable[[str], None]):
        """
        Streams audio to ElevenLabs for STT and calls a callback with transcriptions.
        Args:
            audio_stream: An async generator yielding audio chunks (bytes).
            on_transcription: A callback function to be called with each transcription update.
        """
        logger.info("Starting ElevenLabs STT streaming.")
        await self.elevenlabs_client.stream_stt(audio_stream, on_transcription)
        
    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribes an audio file to text.
        Args:
            file_path: Path to the audio file.
        Returns:
            The transcribed text.
        """
        logger.info(f"Transcribing file: {file_path}")
        try:
            # Use the REST API approach since it's working more reliably
            # ElevenLabs STT REST API endpoint
            url = "https://api.elevenlabs.io/v1/speech-to-text"
            
            headers = {
                "xi-api-key": self.config.elevenlabs_api_key,
                "Accept": "application/json"
            }
            
            # Include model_id in request body using multipart/form-data
            with open(file_path, "rb") as audio_file:
                files = {"file": (Path(file_path).name, audio_file, "audio/wav")}
                data = {
                    "model_id": self.config.model_id,
                    "language": "auto",  # Auto-detect language
                    "languages": self.config.languages
                }
                response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get("text", "")
                logger.info(f"Received transcription: {transcription}")
                return transcription
            else:
                logger.error(f"Error from ElevenLabs API: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return ""

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