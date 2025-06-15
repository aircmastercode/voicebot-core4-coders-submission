#!/usr/bin/env python3
"""
Test script for ElevenLabs Speech-to-Speech functionality.
This script uses ElevenLabs' API to convert speech to speech with a different voice.
"""

import os
import sys
import logging
import argparse
import asyncio
import tempfile
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the Python path
sys.path.append('.')

from modules.eleven_ws import ElevenLabsWebSocketClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_elevenlabs_sts(file_path, output_path=None):
    """
    Test the ElevenLabs STS functionality.
    
    Args:
        file_path: Path to the audio file to convert.
        output_path: Path to save the output audio file. If None, a temporary file is created.
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.error("ELEVENLABS_API_KEY not found in environment variables")
            return None
            
        logger.info(f"Testing ElevenLabs STS with file: {file_path}")
        
        # Create the ElevenLabs client
        client = ElevenLabsWebSocketClient(
            api_key=api_key, 
            model_id="scribe_v1",  # For STT
            voice_id="EXAVITQu4vr4xnSDxMaL"  # For TTS
        )
        
        # Create output file path if not provided
        if not output_path:
            output_path = f"output_speech_{Path(file_path).stem}.wav"
            
        # Open output file for writing
        with open(output_path, "wb") as output_file:
            # Callback to write audio chunks to file
            def on_audio_chunk(chunk):
                output_file.write(chunk)
                logger.info(f"Received STS audio chunk of size: {len(chunk)} bytes")
            
            # Create an async generator to stream the audio file
            async def audio_file_stream():
                chunk_size = 4096  # 4KB chunks
                with open(file_path, "rb") as f:
                    while chunk := f.read(chunk_size):
                        yield chunk
            
            # Stream the audio to ElevenLabs STS
            await client.stream_sts(audio_file_stream(), on_audio_chunk)
            
        logger.info(f"STS conversion complete. Output saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error testing ElevenLabs STS: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ElevenLabs STS with an audio file")
    parser.add_argument("file", help="Path to an audio file to convert")
    parser.add_argument("--output", help="Path to save the output audio file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    output_path = asyncio.run(test_elevenlabs_sts(args.file, args.output))
    if output_path:
        print(f"\nConversion successful. Output saved to: {output_path}\n")
    else:
        print("\nConversion failed.\n")
        sys.exit(1) 