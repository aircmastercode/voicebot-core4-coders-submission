#!/usr/bin/env python3
"""
Audio Capture Module for P2P Lending Voice AI Assistant.

This module provides robust audio capture functionality with:
- Real-time audio recording from various input sources
- Audio device management and selection
- Audio level monitoring and visualization
- Automatic silence detection
- Audio format conversion and handling
"""

import os
import time
import wave
import logging
import threading
import numpy as np
import pyaudio
import soundfile as sf
from queue import Queue
from pydub import AudioSegment
from collections import deque

# Setup logging
logger = logging.getLogger(__name__)


class AudioCapture:
    """Audio capture system for voice input."""
    
    def __init__(self, config):
        """Initialize the audio capture system with configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.audio_config = config.get('audio', {})
        
        # Initialize audio parameters
        self.sample_rate = self.audio_config.get('sample_rate', 16000)
        self.channels = self.audio_config.get('channels', 1)
        self.chunk_size = self.audio_config.get('chunk_size', 1024)
        self.format = pyaudio.paInt16
        self.bit_depth = 16  # For paInt16
        
        # Silence detection parameters
        self.silence_threshold = self.audio_config.get('silence_threshold', 500)
        self.silence_duration = self.audio_config.get('silence_duration', 1.0)
        
        # Audio device selection
        self.device_index = self._get_device_index()
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Audio buffer for streaming
        self.audio_buffer = deque(maxlen=int(self.sample_rate * 60 / self.chunk_size))  # 60 seconds max
        
        # Streaming state
        self.is_streaming = False
        self.stream_thread = None
        self.stream_queue = Queue()
        
        logger.info("Audio capture system initialized")
        
    def _get_device_index(self):
        """Get the index of the preferred audio input device.
        
        Returns:
            int: Device index or None for default device
        """
        preferred_device = self.audio_config.get('preferred_device')
        
        if not preferred_device:
            return None
            
        try:
            audio = pyaudio.PyAudio()
            info = audio.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            for i in range(0, num_devices):
                device_info = audio.get_device_info_by_index(i)
                device_name = device_info.get('name')
                
                if (device_info.get('maxInputChannels') > 0 and 
                    preferred_device.lower() in device_name.lower()):
                    logger.info(f"Selected audio device: {device_name}")
                    audio.terminate()
                    return i
                    
            audio.terminate()
            logger.warning(f"Preferred device '{preferred_device}' not found, using default")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting audio device: {e}")
            return None
    
    def list_devices(self):
        """List available audio input devices.
        
        Returns:
            list: List of available input devices with their indices
        """
        devices = []
        
        try:
            audio = pyaudio.PyAudio()
            info = audio.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            for i in range(0, num_devices):
                device_info = audio.get_device_info_by_index(i)
                
                if device_info.get('maxInputChannels') > 0:
                    devices.append({
                        'index': i,
                        'name': device_info.get('name'),
                        'channels': device_info.get('maxInputChannels'),
                        'sample_rate': int(device_info.get('defaultSampleRate'))
                    })
                    
            audio.terminate()
            
        except Exception as e:
            logger.error(f"Error listing audio devices: {e}")
            
        return devices
    
    def record(self, duration=5):
        """Record audio for specified duration.
        
        Args:
            duration (int): Duration in seconds to record
            
        Returns:
            numpy.ndarray: Audio data as numpy array
            int: Sample rate
        """
        logger.info(f"Recording audio for {duration} seconds")
        
        try:
            # Open audio stream
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.debug("Audio stream opened, recording...")
            print("Recording...")
            
            # Record audio
            frames = []
            for _ in range(0, int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Calculate and display audio level (optional)
                if self.audio_config.get('show_audio_level', False):
                    self._display_audio_level(data)
            
            print("Recording finished.")
            logger.debug("Recording finished")
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            
            return audio_data, self.sample_rate
            
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return np.array([]), self.sample_rate
    
    def start_streaming(self):
        """Start streaming audio capture in a background thread.
        
        Returns:
            bool: True if streaming started successfully
        """
        if self.is_streaming:
            logger.warning("Streaming already active")
            return False
        
        try:
            # Clear buffer and queue
            self.audio_buffer.clear()
            while not self.stream_queue.empty():
                self.stream_queue.get()
            
            # Set streaming flag
            self.is_streaming = True
            
            # Start streaming thread
            self.stream_thread = threading.Thread(target=self._streaming_worker)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            logger.info("Audio streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting audio streaming: {e}")
            self.is_streaming = False
            return False
    
    def stop_streaming(self):
        """Stop streaming audio capture.
        
        Returns:
            bool: True if streaming stopped successfully
        """
        if not self.is_streaming:
            logger.warning("No active streaming to stop")
            return False
        
        try:
            # Clear streaming flag
            self.is_streaming = False
            
            # Wait for thread to finish
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=2.0)
            
            logger.info("Audio streaming stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping audio streaming: {e}")
            return False
    
    def get_next_audio_chunk(self, timeout=None):
        """Get the next audio chunk from the streaming queue.
        
        Args:
            timeout (float, optional): Timeout in seconds
            
        Returns:
            numpy.ndarray: Audio data or None if timeout
            int: Sample rate
        """
        if not self.is_streaming:
            logger.warning("No active streaming")
            return None, self.sample_rate
        
        try:
            # Get chunk from queue
            audio_data = self.stream_queue.get(timeout=timeout)
            return audio_data, self.sample_rate
            
        except Exception:
            return None, self.sample_rate
    
    def _streaming_worker(self):
        """Worker thread for audio streaming."""
        try:
            # Open audio stream
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Initialize silence detection
            silence_chunks = 0
            max_silence_chunks = int(self.silence_duration * self.sample_rate / self.chunk_size)
            frames = []
            
            # Streaming loop
            while self.is_streaming:
                # Read audio chunk
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Add to buffer
                self.audio_buffer.append(data)
                frames.append(data)
                
                # Check for silence to detect end of speech
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_chunk).mean()
                
                if volume < self.silence_threshold:
                    silence_chunks += 1
                else:
                    silence_chunks = 0
                
                # If enough silence detected, process the audio
                if silence_chunks >= max_silence_chunks and len(frames) > max_silence_chunks:
                    # Convert frames to numpy array
                    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                    
                    # Add to queue if not empty
                    if len(audio_data) > 0:
                        self.stream_queue.put(audio_data)
                    
                    # Reset for next utterance
                    frames = []
                    silence_chunks = 0
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            logger.error(f"Error in streaming worker: {e}")
            self.is_streaming = False
    
    def _display_audio_level(self, data):
        """Display audio level visualization in console.
        
        Args:
            data (bytes): Audio data chunk
        """
        audio_chunk = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio_chunk).mean()
        
        # Normalize volume to 0-50 range for display
        level = int(min(50, volume / 100))
        
        # Display audio level bar
        bar = '█' * level + '░' * (50 - level)
        print(f"\rAudio Level: |{bar}| {volume:.0f}", end='')
    
    def save_to_wav(self, audio_data, sample_rate, file_path):
        """Save audio data to WAV file.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            sample_rate (int): Sample rate
            file_path (str): Path to save WAV file
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save as WAV file
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            logger.info(f"Audio saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio to WAV: {e}")
            return False
    
    def convert_format(self, audio_data, sample_rate, target_format='mp3', target_path=None):
        """Convert audio data to different format.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            sample_rate (int): Sample rate
            target_format (str): Target format (mp3, ogg, etc.)
            target_path (str, optional): Path to save converted file
            
        Returns:
            str: Path to converted file or None if failed
        """
        try:
            # Create temporary WAV file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            
            # Save audio data to temporary WAV
            self.save_to_wav(audio_data, sample_rate, temp_wav_path)
            
            # Generate target path if not provided
            if target_path is None:
                target_path = f"{os.path.splitext(temp_wav_path)[0]}.{target_format}"
            
            # Convert using pydub
            audio = AudioSegment.from_wav(temp_wav_path)
            audio.export(target_path, format=target_format)
            
            # Clean up temporary file
            os.remove(temp_wav_path)
            
            logger.info(f"Audio converted to {target_format} at {target_path}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return None
    
    def close(self):
        """Clean up resources."""
        # Stop streaming if active
        if self.is_streaming:
            self.stop_streaming()
        
        # Terminate PyAudio
        if self.audio:
            self.audio.terminate()
            
        logger.info("Audio capture resources released")


# Example usage
if __name__ == "__main__":
    import yaml
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample configuration
    config = {
        'audio': {
            'sample_rate': 16000,
            'channels': 1,
            'chunk_size': 1024,
            'silence_threshold': 500,
            'silence_duration': 1.0,
            'show_audio_level': True
        }
    }
    
    # Create audio capture
    audio_capture = AudioCapture(config)
    
    # List available devices
    devices = audio_capture.list_devices()
    print("Available audio input devices:")
    for device in devices:
        print(f"  {device['index']}: {device['name']} ({device['channels']} channels, {device['sample_rate']} Hz)")
    
    # Record audio
    print("\nRecording 5 seconds of audio...")
    audio_data, sample_rate = audio_capture.record(duration=5)
    
    # Save to WAV file
    audio_capture.save_to_wav(audio_data, sample_rate, "test_recording.wav")
    print(f"Saved recording to test_recording.wav")
    
    # Clean up
    audio_capture.close()
