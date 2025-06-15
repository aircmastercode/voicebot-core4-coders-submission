import logging
from typing import AsyncGenerator, Callable

logger = logging.getLogger(__name__)

"""
PLACEHOLDER MODULE

This module previously contained the ElevenLabsWebSocketClient class for handling
Text-to-Speech (TTS) and Speech-to-Text (STT) streaming via ElevenLabs API.

As part of the refactoring, all ElevenLabs functionality has been moved to the frontend.
This file is kept as a placeholder to maintain backward compatibility with imports.

The ElevenLabs client is now used directly in the frontend JavaScript code.
"""


class ElevenLabsWebSocketClient:
    """
    Placeholder class for backward compatibility.
    All ElevenLabs functionality is now handled in the frontend.
    """
    def __init__(self, api_key: str = None, voice_id: str = None, model_id: str = None):
        self.supported_languages = ["en", "hi"]
        logger.info("ElevenLabsWebSocketClient is now a placeholder. All functionality has been moved to the frontend.")
        
    async def stream_tts(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """Placeholder method that returns empty audio chunks"""
        # Consume the text stream to avoid hanging
        async for _ in text_stream:
            pass
        # Return an empty audio chunk
        yield b''
        
    async def stream_stt(self, audio_stream: AsyncGenerator[bytes, None], on_transcription: Callable[[str], None]):
        """Placeholder method that calls the callback with a message"""
        # Consume the audio stream to avoid hanging
        async for _ in audio_stream:
            pass
        # Call the callback with a message
        on_transcription("Speech recognition is now handled in the frontend.")

