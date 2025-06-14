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
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

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
    
    def upload_to_s3(self, file_path: str, bucket: str, s3_key: str) -> str:
        """
        Upload a file to AWS S3.
        Args:
            file_path: Local path to the file.
            bucket: S3 bucket name.
            s3_key: S3 object key (path in bucket).
        Returns:
            S3 URL of the uploaded file, or empty string if failed.
        """
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        try:
            s3.upload_file(file_path, bucket, s3_key)
            s3_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
            logger.info(f"Uploaded audio to S3: {s3_url}")
            return s3_url
        except (NoCredentialsError, ClientError) as e:
            logger.error(f"Failed to upload to S3: {e}")
            return ""

    def save_audio_to_file(self, audio_data: np.ndarray, filename: str = "temp_recording.wav", upload_s3: bool = False, s3_bucket: Optional[str] = None, s3_key: Optional[str] = None) -> str:
        """
        Save recorded audio to a WAV file.
        
        Args:
            audio_data: The recorded audio as a numpy array.
            filename: The filename to save the audio to.
            upload_s3: If True, upload the audio file to S3.
            s3_bucket: S3 bucket name (required if upload_s3 is True).
            s3_key: S3 object key (required if upload_s3 is True).
        
        Returns:
            The path to the saved audio file, or S3 URL if uploaded.
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
        if upload_s3 and s3_bucket and s3_key:
            s3_url = self.upload_to_s3(filename, s3_bucket, s3_key)
            return s3_url if s3_url else filename
        return filename
    
    def transcribe_file(self, audio_file_path: str, s3_bucket: str, s3_key: str) -> str:
        """
        Transcribe an audio file using Amazon Transcribe.
        Args:
            audio_file_path: Path to the audio file to transcribe.
            s3_bucket: S3 bucket name.
            s3_key: S3 object key.
        Returns:
            The transcribed text.
        """
        # Upload audio to S3
        self.upload_to_s3(audio_file_path, s3_bucket, s3_key)
        import time
        transcribe_client = boto3.client('transcribe', region_name=os.getenv('AWS_REGION'))
        job_name = f"transcribe-job-{int(time.time())}"
        job_uri = f"s3://{s3_bucket}/{s3_key}"
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',
            LanguageCode='en-US'
        )
        # Wait for job to complete
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcript_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            import requests
            transcript_json = requests.get(transcript_url).json()
            return transcript_json['results']['transcripts'][0]['transcript']
        else:
            return ""
        
    def listen_and_transcribe(self, duration: float = 5.0, upload_s3: bool = False, s3_bucket: Optional[str] = None, s3_key: Optional[str] = None) -> str:
        """
        Record audio and transcribe it in one step.
        
        Args:
            duration: The recording duration in seconds.
            upload_s3: If True, upload the audio file to S3.
            s3_bucket: S3 bucket name (required if upload_s3 is True).
            s3_key: S3 object key (required if upload_s3 is True).
        
        Returns:
            The transcribed text.
        """
        # Record audio
        audio_data = self.record_audio(duration)
        
        # Save to temporary file or S3
        temp_file = self.save_audio_to_file(
            audio_data,
            upload_s3=upload_s3,
            s3_bucket=s3_bucket,
            s3_key=s3_key
        )
        
        try:
            # If uploaded to S3, download it temporarily for transcription
            if upload_s3 and temp_file.startswith("https://"):
                import requests
                local_temp = tempfile.mktemp(suffix=".wav")
                with requests.get(temp_file, stream=True) as r:
                    r.raise_for_status()
                    with open(local_temp, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                transcription = self.transcribe_file(local_temp, s3_bucket, s3_key)
                os.remove(local_temp)
                return transcription
            else:
                transcription = self.transcribe_file(temp_file, s3_bucket, s3_key)
                return transcription
        finally:
            # Clean up temporary file if it exists locally and not uploaded to S3
            if not (upload_s3 and temp_file.startswith("https://")):
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