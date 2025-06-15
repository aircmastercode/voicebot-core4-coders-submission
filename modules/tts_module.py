import os
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from dotenv import load_dotenv
import yaml
import uuid

from modules.eleven_ws import ElevenLabsWebSocketClient

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class TTSConfig:
    """Configuration for the TTS module, loaded from config.yaml."""
    
    def __init__(self, voice_id: str = "EXAVITQu4vr4xnSDxMaL", model_id: str = "eleven_monolingual_v1", output_format: str = "mp3", speed: float = 1.0):
        """Initialize TTS configuration with default values."""
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format # Note: ElevenLabs streaming always returns PCM, this might be for file saving
        self.speed = speed # This might not be directly used by streaming API, but can be for post-processing
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "TTSConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            tts_config = config.get("tts", {})
            return cls(
                voice_id=tts_config.get("voice_id", "EXAVITQu4vr4xnSDxMaL"),
                model_id=tts_config.get("model_id", "eleven_monolingual_v1"),
                output_format=tts_config.get("output_format", "mp3"),
                speed=tts_config.get("speed", 1.0)
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class TTSModule:
    """
    Handles Text-to-Speech conversion using ElevenLabs streaming API.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize the TTS module with the provided configuration."""
        self.config = config
        self.elevenlabs_client = ElevenLabsWebSocketClient(
            api_key=self.config.elevenlabs_api_key,
            voice_id=self.config.voice_id,
            model_id=self.config.model_id
        )
        logger.info("TTS Module initialized successfully with ElevenLabs.")
        
    async def stream_text_to_speech(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Converts a stream of text to a stream of speech audio chunks.
        
        Args:
            text_stream: An async generator yielding text chunks.
            
        Returns:
            An async generator yielding audio chunks (bytes).
        """
        logger.info("Starting ElevenLabs TTS streaming.")
        async for audio_chunk in self.elevenlabs_client.stream_tts(text_stream):
            yield audio_chunk

    async def text_to_speech_file(self, text: str, output_filepath: Optional[str] = None) -> Optional[str]:
        """
        Converts text to speech and saves it to a file (non-streaming for file output).
        This uses the streaming client internally but buffers the output.
        
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
            # Create an async generator for the single text input
            async def single_text_generator():
                yield text

            audio_data_buffer = b''
            async for chunk in self.elevenlabs_client.stream_tts(single_text_generator()):
                audio_data_buffer += chunk

            # Save as .wav since ElevenLabs streaming returns raw PCM
            with open(output_filepath, "wb") as f:
                f.write(audio_data_buffer)
            logger.info(f"Text converted to speech and saved to {output_filepath}")
            return output_filepath
            
        except Exception as e:
            logger.error(f"Error during TTS conversion to file: {e}")
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