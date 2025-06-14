#!/usr/bin/env python3
"""
ASR (Automatic Speech Recognition) module for the P2P Lending Voice AI Assistant.

This module handles converting audio input to text using OpenAI's Whisper ASR
or other configured ASR services.
"""

import os
import io
import wave
import tempfile
import logging
import numpy as np
import sounddevice as sd
from typing import Optional, Dict, Any, Tuple

import requests
import yaml
import soundfile as sf
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class ASRConfig:
    """Configuration for the ASR module, loaded from config.yaml."""
    
    def __init__(self, model: str = "whisper-1", language: str = "en"):
        """Initialize ASR configuration with default values."""
        self.model = model
        self.language = language
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "ASRConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            asr_config = config.get("asr", {})
            return cls(
                model=asr_config.get("model", "whisper-1"),
                language=asr_config.get("language", "en")
            )
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return cls()

class ASRModule:
    """
    Handles voice input processing using OpenAI's Whisper ASR.
    """
    
    def __init__(self, config: ASRConfig):
        """Initialize the ASR module with the provided configuration."""
        self.config = config
        self.sample_rate = 16000  # Whisper expects 16kHz audio
        self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
        logger.info("ASR Module initialized successfully.")
        
    def record_audio(self, duration: float = 5.0, show_feedback: bool = True) -> np.ndarray:
        """
        Record audio from the microphone for the specified duration.
        
        Args:
            duration: The recording duration in seconds.
            show_feedback: Whether to show real-time feedback during recording.
            
        Returns:
            The recorded audio as a numpy array.
        """
        if show_feedback:
            print("Listening...")
            
        # Record audio
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1
        )
        
        # Wait for the recording to complete
        sd.wait()
        
        if show_feedback:
            print("Recording complete!")
            
        return recording
    
    def save_audio_to_file(self, audio_data: np.ndarray, filename: str = "temp_recording.wav") -> str:
        """
        Save recorded audio to a WAV file.
        
        Args:
            audio_data: The recorded audio as a numpy array.
            filename: The filename to save the audio to.
            
        Returns:
            The path to the saved audio file.
        """
        # Create a temporary file if no filename is specified
        if filename == "temp_recording.wav":
            fd, filename = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
        
        # Save the audio data to a WAV file
        with sf.SoundFile(filename, mode='w', samplerate=self.sample_rate, 
                          channels=1, subtype='PCM_16') as f:
            f.write(audio_data)
            
        logger.info(f"Audio saved to {filename}")
        return filename
    
    def transcribe_file(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file using OpenAI's Whisper ASR.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            
        Returns:
            The transcribed text.
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.openai_client.audio.transcriptions.create(
                    model=self.config.model,
                    file=audio_file,
                    language=self.config.language
                )
                
            transcription = response.text
            logger.info(f"Transcription completed: '{transcription}'")
            return transcription
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""
        
    def listen_and_transcribe(self, duration: float = 5.0) -> str:
        """
        Record audio and transcribe it in one step.
        
        Args:
            duration: The recording duration in seconds.
            
        Returns:
            The transcribed text.
        """
        # Record audio
        audio_data = self.record_audio(duration)
        
        # Save to temporary file
        temp_file = self.save_audio_to_file(audio_data)
        
        try:
            # Transcribe
            transcription = self.transcribe_file(temp_file)
            return transcription
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    def continuous_listening(self, callback, silence_threshold: float = 0.03, 
                             min_silence_duration: float = 1.0, 
                             max_listen_time: float = 30.0):
        """
        Listen continuously until silence is detected.
        
        Args:
            callback: Function to call with the transcribed text
            silence_threshold: Threshold for detecting silence
            min_silence_duration: Minimum duration of silence to end recording
            max_listen_time: Maximum recording time
        """
        # Implementation requires more complex audio processing and silence detection
        # This is a placeholder for now
        pass


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        asr_config = ASRConfig.from_yaml()
        asr = ASRModule(config=asr_config)
        
        print("Say something...")
        text = asr.listen_and_transcribe(duration=5.0)
        print(f"You said: {text}")
        
    except Exception as e:
        logger.error(f"Error in ASR module example: {e}") 