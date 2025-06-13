#!/usr/bin/env python3
"""
Automatic Speech Recognition (ASR) Module for P2P Lending Voice AI Assistant.

This module handles voice input processing, including:
- Audio capture from microphone
- Noise cancellation and audio preprocessing
- Speech-to-text conversion with multilingual support
- Language detection for automatic language switching
"""

import os
import time
import logging
import tempfile
import numpy as np
import soundfile as sf
import wave
import librosa
from pydub import AudioSegment
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Import custom modules
from modules.language_detection import LanguageDetector
from modules.audio_capture import AudioCapture
from modules.audio_preprocessing import AudioPreprocessor

# Setup logging
logger = logging.getLogger(__name__)


class ASR:
    """Automatic Speech Recognition class for voice input processing."""
    
    def __init__(self, config):
        """Initialize the ASR module with configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.asr_config = config.get('asr', {})
        self.audio_config = config.get('audio', {})
        
        # Initialize audio parameters
        self.sample_rate = self.audio_config.get('sample_rate', 16000)
        self.channels = self.audio_config.get('channels', 1)
        self.chunk_size = self.audio_config.get('chunk_size', 1024)
        self.format = pyaudio.paInt16
        
        # Initialize ASR client
        self.provider = self.asr_config.get('provider', 'openai')
        self.asr_client = self._initialize_asr_client()
        
        # Language settings
        self.default_language = self.config.get('languages', {}).get('default', 'en')
        self.supported_languages = self.config.get('languages', {}).get('supported', ['en', 'hi'])
        
        # Initialize language detector
        self.language_detector = LanguageDetector(config)
        
        # Initialize audio capture system
        self.audio_capture = AudioCapture(config)
        
        # Initialize audio preprocessor
        self.audio_preprocessor = AudioPreprocessor(config)
        
        logger.info(f"ASR module initialized with provider: {self.provider}")
    
    def _initialize_asr_client(self):
        """Initialize the ASR client based on the configured provider.
        
        Returns:
            object: ASR client instance
        """
        if self.provider == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            return OpenAI(api_key=api_key)
        
        elif self.provider == 'azure':
            # Azure Speech SDK implementation
            raise NotImplementedError("Azure ASR not yet implemented")
        
        elif self.provider == 'google':
            # Google Speech-to-Text implementation
            raise NotImplementedError("Google ASR not yet implemented")
        
        else:
            raise ValueError(f"Unsupported ASR provider: {self.provider}")
    
    def _map_language_to_provider(self, language_code):
        """Map internal language code to provider-specific code.
        
        Args:
            language_code (str): Internal language code
            
        Returns:
            str: Provider-specific language code
        """
        # Language code mapping for different providers
        if self.provider == 'openai':
            # OpenAI Whisper language codes
            # For Hinglish, we use 'auto' to let Whisper detect the language mix
            mapping = {
                'en': 'en',      # English
                'hi': 'hi',      # Hindi
                'hi-en': 'auto'  # Hinglish (mixed Hindi-English)
            }
            return mapping.get(language_code, 'auto')
            
        elif self.provider == 'azure':
            # Azure Speech language codes
            mapping = {
                'en': 'en-US',   # English (US)
                'hi': 'hi-IN',   # Hindi (India)
                'hi-en': 'en-IN'  # English (Indian) - closest to Hinglish
            }
            return mapping.get(language_code, 'en-US')
            
        elif self.provider == 'google':
            # Google Speech-to-Text language codes
            mapping = {
                'en': 'en-US',   # English (US)
                'hi': 'hi-IN',   # Hindi (India)
                'hi-en': 'en-IN'  # English (Indian) - closest to Hinglish
            }
            return mapping.get(language_code, 'en-US')
            
        # Default: return the original code
        return language_code
    
    def capture_audio(self, duration=5):
        """Capture audio from microphone using the audio capture module.
        
        Args:
            duration (int): Duration in seconds to record
            
        Returns:
            numpy.ndarray: Audio data as numpy array
            int: Sample rate
        """
        logger.info(f"Capturing {duration}s of audio")
        
        try:
            # Use the dedicated audio capture module
            audio_data, sample_rate = self.audio_capture.record(duration=duration)
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"Error capturing audio: {e}")
            return np.array([]), self.audio_config.get('sample_rate', 16000)
    
    def preprocess_audio(self, audio_data, sample_rate):
        """Apply preprocessing to audio data using the AudioPreprocessor module.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        logger.info("Preprocessing audio data")
        
        try:
            # Use the dedicated audio preprocessor module
            processed_audio, processed_sample_rate = self.audio_preprocessor.process(audio_data, sample_rate)
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return audio_data
    
    def save_audio_to_file(self, audio_data, sample_rate, file_path=None):
        """Save audio data to a temporary WAV file.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            sample_rate (int): Sample rate of audio data
            file_path (str, optional): Path to save audio file
            
        Returns:
            str: Path to saved audio file
        """
        if file_path is None:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                file_path = temp_file.name
        
        # Save audio to file
        sf.write(file_path, audio_data, sample_rate)
        logger.debug(f"Audio saved to {file_path}")
        
        return file_path
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def transcribe_audio(self, audio_file, language=None):
        """Transcribe audio file to text using configured ASR provider.
        
        Args:
            audio_file (str): Path to audio file
            language (str, optional): Language code for transcription
            
        Returns:
            dict: Transcription result with text, language, and confidence
        """
        logger.info(f"Transcribing audio with {self.provider}")
        
        # Set language or use auto-detection
        detect_language = language is None
        language = language or self.default_language
        
        # Map language code to provider-specific code if needed
        provider_language = self._map_language_to_provider(language)
        
        start_time = time.time()
        
        try:
            if self.provider == 'openai':
                with open(audio_file, "rb") as audio:
                    model = self.asr_config.get('model', 'whisper-1')
                    response = self.asr_client.audio.transcriptions.create(
                        model=model,
                        file=audio,
                        language=None if detect_language else provider_language,
                        response_format="verbose_json"
                    )
                
                # Extract results
                transcribed_text = response.text
                detected_language = getattr(response, 'language', language)
                
                # If language wasn't specified, use our language detector for better detection
                # especially for Hinglish which OpenAI might not properly identify
                if detect_language:
                    detected_language = self.language_detector.detect_language(transcribed_text)
                
                result = {
                    'text': transcribed_text,
                    'language': detected_language,
                    'confidence': getattr(response, 'confidence', 1.0)
                }
            
            else:
                # Placeholder for other providers
                raise NotImplementedError(f"{self.provider} transcription not implemented")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Transcription completed in {elapsed_time:.2f}s")
            logger.debug(f"Transcription result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def transcribe_with_language_detection(self, audio_data=None, audio_file=None):
        """Transcribe audio with automatic language detection.
        
        Args:
            audio_data (numpy.ndarray, optional): Audio data as numpy array
            audio_file (str, optional): Path to audio file
            
        Returns:
            dict: Transcription result with text, language, and confidence
        """
        logger.info("Transcribing with language detection")
        
        # First pass: transcribe with auto language detection
        initial_result = self.transcribe(audio_data, audio_file, language='auto')
        
        if not initial_result or not initial_result.get('text'):
            logger.warning("Initial transcription failed or returned empty text")
            return initial_result
        
        # Use language detector to identify the language more accurately
        detected_language = self.language_detector.detect_language(initial_result['text'])
        logger.info(f"Detected language: {detected_language}")
        
        # For Hinglish or if the detected language matches the initial detection, return the result
        if detected_language == 'hi-en' or detected_language == initial_result.get('language'):
            # Update the language in the result
            initial_result['language'] = detected_language
            return initial_result
        
        # For other languages, if the detected language differs from initial detection,
        # re-transcribe with the detected language for better accuracy
        logger.info(f"Re-transcribing with detected language: {detected_language}")
        final_result = self.transcribe(audio_data, audio_file, language=detected_language)
        
        return final_result
    
    def transcribe(self, audio_data=None, audio_file=None, language=None):
        """Transcribe audio data or file to text.
        
        Args:
            audio_data (numpy.ndarray, optional): Audio data as numpy array
            audio_file (str, optional): Path to audio file
            language (str, optional): Language code for transcription
            
        Returns:
            dict: Transcription result with text, language, and confidence
        """
        logger.info("Transcribing audio")
        
        # Validate input
        if audio_data is None and audio_file is None:
            logger.error("No audio data or file provided for transcription")
            return {'text': '', 'language': self.default_language, 'confidence': 0.0}
        
        try:
            # If audio data is provided, save to temporary file
            temp_file = None
            if audio_file is None and audio_data is not None:
                audio_file = self.save_audio_to_file(audio_data, self.sample_rate)
                temp_file = audio_file
            
            # Transcribe audio file
            result = self.transcribe_audio(audio_file, language)
            
            # Clean up temporary file if created
            if temp_file:
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            
            # Post-process transcription for the detected language
            result = self._post_process_transcription(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in transcribe: {e}")
            return {'text': '', 'language': self.default_language, 'confidence': 0.0}
    
    def _post_process_transcription(self, result):
        """Post-process transcription based on detected language.
        
        Args:
            result (dict): Transcription result
            
        Returns:
            dict: Post-processed transcription result
        """
        if not result or not result.get('text'):
            return result
            
        text = result['text']
        language = result.get('language', self.default_language)
        
        # Apply language-specific post-processing
        if language == 'hi':
            # Hindi-specific processing (e.g., fix common Hindi transcription errors)
            # This is a placeholder for actual Hindi-specific processing
            pass
            
        elif language == 'hi-en':
            # Hinglish-specific processing
            # This is a placeholder for actual Hinglish-specific processing
            pass
            
        elif language == 'en':
            # English-specific processing
            # This is a placeholder for actual English-specific processing
            pass
        
        # Update the text in the result
        result['text'] = text
        
        return result
    
    def stream_transcribe(self, callback=None, buffer_size=3, interim_results=True):
        """Stream audio and transcribe in real-time.
        
        Args:
            callback (callable, optional): Callback function to receive transcription results
            buffer_size (int): Size of audio buffer in seconds before processing
            interim_results (bool): Whether to return interim results or wait for final
            
        Returns:
            None: Results are delivered via callback
        """
        logger.info("Starting streaming transcription")
        
        if callback is None:
            logger.warning("No callback provided for streaming transcription")
            callback = lambda x: logger.info(f"Transcription: {x}")
        
        # Configure streaming parameters
        self.streaming_config = {
            'buffer_size': buffer_size,
            'interim_results': interim_results,
            'active': True,
            'callback': callback,
            'buffer': [],
            'last_process_time': time.time(),
            'silence_threshold': self.audio_config.get('silence_threshold', 0.03),
            'silence_duration': self.audio_config.get('silence_duration', 1.0),
            'min_audio_length': self.audio_config.get('min_audio_length', 0.5)
        }
        
        # Start audio capture in streaming mode
        self.audio_capture.start_streaming(self._process_audio_chunk)
        
        logger.info("Streaming transcription started")
    
    def stop_streaming(self):
        """Stop streaming transcription.
        
        Returns:
            None
        """
        logger.info("Stopping streaming transcription")
        
        if not hasattr(self, 'streaming_config') or not self.streaming_config.get('active', False):
            logger.warning("Streaming transcription not active")
            return
        
        # Process any remaining audio in the buffer
        if self.streaming_config['buffer']:
            self._process_buffer(final=True)
        
        # Stop audio capture streaming
        self.audio_capture.stop_streaming()
        
        # Update streaming state
        self.streaming_config['active'] = False
        
        logger.info("Streaming transcription stopped")
    
    def _process_audio_chunk(self, audio_chunk, sample_rate):
        """Process audio chunk from streaming capture.
        
        Args:
            audio_chunk (numpy.ndarray): Audio chunk data
            sample_rate (int): Sample rate of audio data
            
        Returns:
            None
        """
        if not hasattr(self, 'streaming_config') or not self.streaming_config.get('active', False):
            return
        
        # Add chunk to buffer
        self.streaming_config['buffer'].append(audio_chunk)
        
        # Check if we have enough audio to process
        buffer_duration = len(self.streaming_config['buffer']) * (len(audio_chunk) / sample_rate)
        current_time = time.time()
        time_since_last = current_time - self.streaming_config['last_process_time']
        
        # Process buffer if it's full or if we've detected silence
        if buffer_duration >= self.streaming_config['buffer_size'] or time_since_last >= self.streaming_config['silence_duration']:
            self._process_buffer()
            
    def _process_buffer(self, final=False):
        """Process accumulated audio buffer.
        
        Args:
            final (bool): Whether this is the final processing of the buffer
            
        Returns:
            None
        """
        if not self.streaming_config['buffer']:
            return
        
        # Concatenate audio chunks
        audio_data = np.concatenate(self.streaming_config['buffer'])
        
        # Check if audio is too short
        audio_duration = len(audio_data) / self.sample_rate
        if audio_duration < self.streaming_config['min_audio_length'] and not final:
            return
        
        # Preprocess audio
        processed_audio = self.preprocess_audio(audio_data, self.sample_rate)
        
        # Check if audio is mostly silence
        if np.max(np.abs(processed_audio)) < self.streaming_config['silence_threshold'] and not final:
            # Clear buffer and reset timer if it's just silence
            self.streaming_config['buffer'] = []
            self.streaming_config['last_process_time'] = time.time()
            return
        
        try:
            # Save to temporary file
            audio_file = self.save_audio_to_file(processed_audio, self.sample_rate)
            
            # Transcribe with language detection
            result = self.transcribe_with_language_detection(audio_file=audio_file)
            
            # Clean up temporary file
            try:
                os.remove(audio_file)
            except OSError:
                pass
            
            # Call the callback with the result
            if result and result.get('text') and callable(self.streaming_config['callback']):
                self.streaming_config['callback'](result)
                
        except Exception as e:
            logger.error(f"Error processing streaming audio buffer: {e}")
        
        # Clear buffer and reset timer
        self.streaming_config['buffer'] = []
        self.streaming_config['last_process_time'] = time.time()
    
    def close(self):
        """Clean up resources."""
        # Clean up audio capture resources
        if hasattr(self, 'audio_capture'):
            self.audio_capture.close()
            
        logger.info("ASR module resources released")
# Example usage
if __name__ == "__main__":
    import yaml
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    with open("../config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Create ASR instance
    asr = ASR(config)
    
    # Test transcription
    print("Say something...")
    text = asr.transcribe(duration=5)
    print(f"You said: {text}")