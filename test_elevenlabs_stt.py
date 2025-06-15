#!/usr/bin/env python3
"""
Test script for ElevenLabs Speech-to-Text functionality.
This script uses ElevenLabs' API to transcribe audio files.
"""

import os
import sys
import logging
import argparse
import asyncio
import requests
import json
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

async def test_elevenlabs_stt(file_path):
    """
    Test the ElevenLabs STT using their WebSocket API.
    
    Args:
        file_path: Path to the audio file to transcribe.
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.error("ELEVENLABS_API_KEY not found in environment variables")
            return None
            
        logger.info(f"Testing ElevenLabs STT with file: {file_path}")
        
        # Create the ElevenLabs client
        client = ElevenLabsWebSocketClient(api_key=api_key, model_id="scribe_v1")
        
        # Store transcription results
        transcription_results = []
        
        def on_transcription(transcript):
            logger.info(f"Received transcription: {transcript}")
            transcription_results.append(transcript)
        
        # Create an async generator to stream the audio file
        async def audio_file_stream():
            chunk_size = 4096  # 4KB chunks
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        
        # Stream the audio to ElevenLabs STT
        await client.stream_stt(audio_file_stream(), on_transcription)
        
        # Return the final transcription (should be the last one received)
        final_transcription = transcription_results[-1] if transcription_results else ""
        print(f"\nTranscription result: {final_transcription}\n")
        return final_transcription
        
    except Exception as e:
        logger.error(f"Error testing ElevenLabs STT: {e}")
        return None

# Alternative approach using REST API (if available)
def test_elevenlabs_stt_rest(file_path):
    """
    Test ElevenLabs STT using their REST API (if available).
    
    Args:
        file_path: Path to the audio file to transcribe.
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.error("ELEVENLABS_API_KEY not found in environment variables")
            return None
            
        logger.info(f"Testing ElevenLabs STT REST API with file: {file_path}")
        
        # ElevenLabs STT REST API endpoint
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        
        headers = {
            "xi-api-key": api_key,
            "Accept": "application/json"
        }
        
        # Include model_id in request body using multipart/form-data
        with open(file_path, "rb") as audio_file:
            files = {"file": (Path(file_path).name, audio_file, "audio/wav")}
            data = {"model_id": "scribe_v1"}
            response = requests.post(url, headers=headers, data=data, files=files)
        
        if response.status_code == 200:
            result = response.json()
            transcription = result.get("text", "")
            logger.info(f"Received transcription: {transcription}")
            print(f"\nTranscription result: {transcription}\n")
            return transcription
        else:
            logger.error(f"Error from ElevenLabs API: {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"Error testing ElevenLabs STT REST API: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ElevenLabs STT with an audio file")
    parser.add_argument("file", help="Path to an audio file to transcribe")
    parser.add_argument("--rest", action="store_true", help="Use REST API instead of WebSocket")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    if args.rest:
        test_elevenlabs_stt_rest(args.file)
    else:
        asyncio.run(test_elevenlabs_stt(args.file)) 