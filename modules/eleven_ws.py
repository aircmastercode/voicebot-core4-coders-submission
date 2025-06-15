import asyncio
import websockets
import json
import logging
import asyncio
import base64
from typing import AsyncGenerator, Optional, Callable

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ElevenLabsWebSocketClient:
    """
    A WebSocket client for ElevenLabs Text-to-Speech (TTS) and Speech-to-Text (STT) streaming.
    """
    def __init__(self, api_key: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL", model_id: str = "eleven_monolingual_v1"): # Default voice and model for demonstration
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.websocket = None
        self.uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id={self.model_id}"
        self.is_connected = False

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info("Connected to ElevenLabs WebSocket.")

            # Send the initial message with API key and other parameters
            await self.websocket.send(json.dumps({
                "text": " ", # Initial handshake message
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                "xi_api_key": self.api_key,
            }))
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ElevenLabs WebSocket: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from ElevenLabs WebSocket.")

    async def stream_tts(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Streams text to ElevenLabs and yields audio chunks.
        """
        if not self.is_connected:
            if not await self.connect():
                return

        try:
            async for text_chunk in text_stream:
                if text_chunk:
                    await self.websocket.send(json.dumps({"text": text_chunk, "try_trigger_generation": True}))

            await self.websocket.send(json.dumps({"text": ""})) # End of stream marker

            async for message in self.websocket:
                data = json.loads(message)
                if "audio" in data and data["audio"]:
                    yield base64.b64decode(data["audio"])
                elif "is_final" in data and data["is_final"]:
                    break
                elif "error" in data:
                    logger.error(f"ElevenLabs TTS error: {data['message']}")
                    break
        except Exception as e:
            logger.error(f"Error during ElevenLabs TTS streaming: {e}")
        finally:
            await self.disconnect()

    async def stream_stt(self, audio_stream: AsyncGenerator[bytes, None], on_transcription: Callable[[str], None]):
        """
        Streams audio to ElevenLabs for STT and calls a callback with transcriptions.
        """
        # The proper URL for ElevenLabs Speech-to-Text WebSocket API
        # Note: As of the latest information, ElevenLabs may not support WebSocket STT
        # So this might still fail
        stt_uri = f"wss://api.elevenlabs.io/v1/speech-to-text/streaming?model_id={self.model_id}"
        
        try:
            async with websockets.connect(stt_uri) as ws:
                # Send initiation message with API key in the headers
                await ws.send(json.dumps({
                    "xi_api_key": self.api_key,  # Use xi_api_key instead of api_key
                    "sample_rate": 16000, # ElevenLabs STT expects 16kHz
                    "language": "en" # Assuming English for now
                }))

                # Task to send audio
                async def send_audio():
                    try:
                        async for chunk in audio_stream:
                            await ws.send(chunk)
                        await ws.send(json.dumps({"eof": True})) # End of audio stream
                    except Exception as e:
                        logger.error(f"Error sending audio for STT: {e}")

                # Task to receive transcriptions
                async def receive_transcriptions():
                    try:
                        async for message in ws:
                            data = json.loads(message)
                            if "transcript" in data:
                                on_transcription(data["transcript"])
                            elif "error" in data:
                                logger.error(f"ElevenLabs STT error: {data['message']}")
                                break
                    except Exception as e:
                        logger.error(f"Error receiving transcriptions from STT: {e}")

                await asyncio.gather(send_audio(), receive_transcriptions())

        except Exception as e:
            logger.error(f"Failed to connect or stream STT: {e}")

    async def stream_sts(self, audio_stream: AsyncGenerator[bytes, None], on_audio_chunk: Callable[[bytes], None]):
        """
        Streams audio to ElevenLabs for STS (Speech-to-Speech) and calls a callback with converted audio chunks.
        This implementation combines STT and TTS to achieve speech-to-speech functionality.
        """
        try:
            # Step 1: First transcribe the audio using STT
            transcription_results = []
            
            def on_transcription(transcript):
                logger.info(f"STS intermediate transcription: {transcript}")
                transcription_results.append(transcript)
            
            # Use our existing stream_stt method
            await self.stream_stt(audio_stream, on_transcription)
            
            # Get the final transcription
            final_transcription = transcription_results[-1] if transcription_results else ""
            
            if not final_transcription:
                logger.error("STS failed: No transcription produced")
                return
                
            logger.info(f"STS transcription complete: {final_transcription}")
            
            # Step 2: Now convert the transcription to speech using TTS
            async def text_generator():
                yield final_transcription
                
            # Use our existing stream_tts method
            async for audio_chunk in self.stream_tts(text_generator()):
                # Pass the audio chunk to the callback
                on_audio_chunk(audio_chunk)
                
        except Exception as e:
            logger.error(f"Failed to perform speech-to-speech conversion: {e}")

# Example Usage (for TTS)
async def main():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment variables.")
        return

    client = ElevenLabsWebSocketClient(api_key=api_key)

    async def text_generator():
        yield "Hello, "
        await asyncio.sleep(0.5)
        yield "this is a test of the "
        await asyncio.sleep(0.5)
        yield "ElevenLabs streaming TTS API."

    print("Starting TTS stream...")
    audio_chunks = client.stream_tts(text_generator())
    async for chunk in audio_chunks:
        # In a real application, you would play this audio chunk
        # For demonstration, we'll just print its size
        print(f"Received audio chunk of size: {len(chunk)} bytes")

    print("TTS stream finished.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
