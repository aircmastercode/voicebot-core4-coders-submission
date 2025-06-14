#!/usr/bin/env python3
"""
TTS (Text-to-Speech) module for the P2P Lending Voice AI Assistant.

This module handles converting text responses to speech using OpenAI's TTS API
or other configured TTS services.
"""

import os
import io
import logging
import tempfile
from typing import Optional, Dict, Any
import yaml
import soundfile as sf
import numpy as np
import sounddevice as sd
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class TTSConfig:
    """Configuration for the TTS module, loaded from config.yaml."""
    
    def __init__(self, 
                 model: str = "tts-1", 
                 voice: str = "alloy", 
                 output_format: str = "mp3",
                 speed: float = 1.0):
        """Initialize TTS configuration with default values."""
        self.model = model
        self.voice = voice
        self.output_format = output_format
        self.speed = speed
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "TTSConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            tts_config = config.get("tts", {})
            return cls(
                model=tts_config.get("model", "tts-1"),
                voice=tts_config.get("voice", "alloy"),
                output_format=tts_config.get("output_format", "mp3"),
                speed=tts_config.get("speed", 1.0)
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class TTSModule:
    """
    Handles text-to-speech conversion using OpenAI's TTS API.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize the TTS module with the provided configuration."""
        self.config = config
        self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
        logger.info("TTS Module initialized successfully.")
        
    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Convert text to speech and save to a file.
        
        Args:
            text: Text to convert to speech
            output_file: Path to save the audio file. If None, a temporary file is created.
            
        Returns:
            The path to the generated audio file
        """
        if not text:
            logger.warning("Empty text provided for TTS")
            return ""
            
        # Create a temporary file if no output file is specified
        if output_file is None:
            fd, output_file = tempfile.mkstemp(suffix=f".{self.config.output_format}")
            os.close(fd)
            
        try:
            logger.info(f"Converting text to speech: '{text[:50]}...'")
            
            response = self.openai_client.audio.speech.create(
                model=self.config.model,
                voice=self.config.voice,
                input=text,
                speed=self.config.speed
            )
            
            # Save to file
            response.stream_to_file(output_file)
            logger.info(f"Audio saved to {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during text-to-speech conversion: {e}")
            return ""
            
    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the audio file
            audio_file = self.text_to_speech(text)
            if not audio_file:
                return False
                
            # Play the audio file
            data, samplerate = sf.read(audio_file)
            sd.play(data, samplerate)
            sd.wait()  # Wait until playback is finished
            
            # Clean up the temporary file
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return True
            
        except Exception as e:
            logger.error(f"Error playing speech: {e}")
            return False
            
    def add_speech_markers(self, text: str) -> str:
        """
        Add SSML speech markers to make the output more natural.
        
        Args:
            text: Text to add speech markers to
            
        Returns:
            Text with speech markers
        """
        # Simple implementation - can be expanded with more sophisticated SSML
        # This depends on the TTS engine's capabilities
        return text

# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        tts_config = TTSConfig.from_yaml()
        tts = TTSModule(config=tts_config)
        
        result = tts.speak("Hello! I am your P2P lending assistant. How can I help you today?")
        if result:
            print("Speech played successfully")
        else:
            print("Failed to play speech")
            
    except Exception as e:
        logger.error(f"Error in TTS module example: {e}") 