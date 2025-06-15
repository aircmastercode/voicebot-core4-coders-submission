import os
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from dotenv import load_dotenv
import yaml
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class TTSConfig:
    """Configuration for the TTS module, loaded from config.yaml."""
    
    def __init__(self, output_format: str = "mp3", speed: float = 1.0, languages: list = None):
        """Initialize TTS configuration with default values."""
        self.output_format = output_format
        self.speed = speed
        self.languages = languages or ["en", "hi"]  # Default to English and Hindi
        
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "TTSConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            tts_config = config.get("tts", {})
            return cls(
                output_format=tts_config.get("output_format", "mp3"),
                speed=tts_config.get("speed", 1.0),
                languages=tts_config.get("languages", ["en", "hi"])
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class TTSModule:
    """
    Handles Text-to-Speech conversion (frontend implementation).
    This is now a mock implementation since TTS is handled in the frontend.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize the TTS module with the provided configuration."""
        self.config = config
        logger.info(f"TTS Module initialized successfully. Languages: {', '.join(self.config.languages)}")
        
    async def stream_text_to_speech(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Mock implementation for text-to-speech streaming.
        
        Args:
            text_stream: An async generator yielding text chunks.
            
        Returns:
            An async generator yielding empty audio chunks (bytes).
        """
        logger.info("TTS is now handled in the frontend. This is a mock implementation.")
        # Just consume the text stream to avoid hanging
        full_text = ""
        async for text in text_stream:
            full_text += text
            
        # Return an empty audio chunk to maintain the interface
        yield b''

    async def text_to_speech_file(self, text: str, output_filepath: Optional[str] = None) -> Optional[str]:
        """
        Mock implementation for text-to-speech file generation.
        
        Args:
            text: The text to convert.
            output_filepath: The path to save the generated audio file. If None, a temporary file is created.
            
        Returns:
            The path to the generated audio file, or None if an error occurred.
        """
        if not text:
            logger.warning("No text provided for TTS conversion.")
            return None

        if not output_filepath:
            output_filepath = f"temp_audio_{uuid.uuid4()}.wav"  # Always use .wav extension
        else:
            # Ensure the output filepath has a .wav extension
            output_filepath = os.path.splitext(output_filepath)[0] + ".wav"

        try:
            # Create a simple empty WAV file (8-bit PCM, 1 channel, 8000 Hz)
            # This is just a placeholder since TTS is now handled in the frontend
            with open(output_filepath, "wb") as f:
                # Write a minimal WAV header
                f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00')
                
            logger.info(f"Mock TTS: Created empty audio file at {output_filepath}")
            return output_filepath
            
        except Exception as e:
            logger.error(f"Error creating mock audio file: {e}")
            return None

# Example usage
async def main():
    logging.basicConfig(level=logging.INFO)
    
    try:
        tts_config = TTSConfig.from_yaml()
        tts = TTSModule(config=tts_config)
        
        text_to_convert = "Hello, this is a test of the ElevenLabs streaming Text-to-Speech module."
        
        # Example of streaming TTS
        async def text_gen():
            yield text_to_convert

        print("Streaming TTS...")
        async for chunk in tts.stream_text_to_speech(text_gen()):
            # In a real app, you'd play this audio chunk
            print(f"Received streaming audio chunk of size: {len(chunk)} bytes")

        # Example of saving to file (buffers entire audio then saves)
        output_file = await tts.text_to_speech_file(text_to_convert, "test_output.wav")
        if output_file:
            print(f"Audio saved to: {output_file}")
        else:
            print("TTS file conversion failed.")
            
    except Exception as e:
        logger.error(f"Error in TTS module example: {e}")

if __name__ == '__main__':
    asyncio.run(main())