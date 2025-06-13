#!/usr/bin/env python3
"""
Audio Preprocessing Module for P2P Lending Voice AI Assistant.

This module provides advanced audio preprocessing functionality including:
- Noise reduction with configurable parameters
- Audio normalization
- Silence removal
- Audio filtering (low-pass, high-pass, band-pass)
- Signal enhancement
"""

import logging
import numpy as np
import librosa
import noisereduce as nr
from scipy import signal
from scipy.signal import butter, lfilter, filtfilt

# Setup logging
logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """Advanced audio preprocessing for improved ASR accuracy."""
    
    def __init__(self, config):
        """Initialize the audio preprocessor with configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.audio_config = config.get('audio', {})
        self.preprocessing_config = self.audio_config.get('preprocessing', {})
        
        # Noise reduction parameters
        self.noise_reduction_enabled = self.preprocessing_config.get('noise_reduction_enabled', True)
        self.noise_reduction_strength = self.preprocessing_config.get('noise_reduction_strength', 0.5)
        self.noise_reduction_stationary = self.preprocessing_config.get('stationary', True)
        
        # Normalization parameters
        self.normalization_enabled = self.preprocessing_config.get('normalization_enabled', True)
        self.target_db = self.preprocessing_config.get('target_db', -20)
        
        # Filtering parameters
        self.filtering_enabled = self.preprocessing_config.get('filtering_enabled', False)
        self.filter_type = self.preprocessing_config.get('filter_type', 'bandpass')
        self.low_cutoff = self.preprocessing_config.get('low_cutoff', 80)
        self.high_cutoff = self.preprocessing_config.get('high_cutoff', 7500)
        self.filter_order = self.preprocessing_config.get('filter_order', 4)
        
        # Silence removal parameters
        self.silence_removal_enabled = self.preprocessing_config.get('silence_removal_enabled', True)
        self.silence_threshold = self.preprocessing_config.get('silence_threshold', 0.03)
        self.min_silence_duration = self.preprocessing_config.get('min_silence_duration', 0.3)
        
        # Enhancement parameters
        self.enhancement_enabled = self.preprocessing_config.get('enhancement_enabled', False)
        self.enhancement_method = self.preprocessing_config.get('enhancement_method', 'spectral_subtraction')
        
        logger.info("Audio preprocessor initialized")
    
    def process(self, audio_data, sample_rate):
        """Apply all configured preprocessing steps to audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Processed audio data
            int: Sample rate (may be changed by processing)
        """
        logger.info("Processing audio data")
        
        # Convert to float32 for processing if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / 32768.0
        
        # Apply preprocessing steps based on configuration
        if self.noise_reduction_enabled:
            audio_data = self.reduce_noise(audio_data, sample_rate)
        
        if self.filtering_enabled:
            audio_data = self.apply_filter(audio_data, sample_rate)
        
        if self.silence_removal_enabled:
            audio_data = self.remove_silence(audio_data, sample_rate)
        
        if self.enhancement_enabled:
            audio_data = self.enhance_signal(audio_data, sample_rate)
        
        if self.normalization_enabled:
            audio_data = self.normalize_audio(audio_data)
        
        # Convert back to int16 if needed
        if self.preprocessing_config.get('output_format', 'float32') == 'int16':
            audio_data = np.clip(audio_data * 32768.0, -32768, 32767).astype(np.int16)
        
        return audio_data, sample_rate
    
    def reduce_noise(self, audio_data, sample_rate):
        """Apply noise reduction to audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Noise-reduced audio data
        """
        logger.debug("Applying noise reduction")
        
        try:
            # Determine noise reduction parameters based on strength
            prop_decrease = self.noise_reduction_strength
            
            # Apply noise reduction
            reduced_noise = nr.reduce_noise(
                y=audio_data,
                sr=sample_rate,
                stationary=self.noise_reduction_stationary,
                prop_decrease=prop_decrease
            )
            
            return reduced_noise
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return audio_data
    
    def normalize_audio(self, audio_data):
        """Normalize audio to target dB level.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            
        Returns:
            numpy.ndarray: Normalized audio data
        """
        logger.debug("Normalizing audio")
        
        try:
            # Calculate current dB level
            rms = np.sqrt(np.mean(audio_data**2))
            current_db = 20 * np.log10(rms) if rms > 0 else -80
            
            # Calculate gain needed to reach target dB
            gain = 10**((self.target_db - current_db) / 20)
            
            # Apply gain with clipping prevention
            normalized = audio_data * gain
            
            # Prevent clipping
            if np.max(np.abs(normalized)) > 1.0:
                normalized = normalized / np.max(np.abs(normalized))
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error in audio normalization: {e}")
            return audio_data
    
    def apply_filter(self, audio_data, sample_rate):
        """Apply audio filtering (low-pass, high-pass, or band-pass).
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Filtered audio data
        """
        logger.debug(f"Applying {self.filter_type} filter")
        
        try:
            nyquist = 0.5 * sample_rate
            
            if self.filter_type == 'lowpass':
                # Low-pass filter
                cutoff = self.high_cutoff / nyquist
                b, a = butter(self.filter_order, cutoff, btype='low')
                
            elif self.filter_type == 'highpass':
                # High-pass filter
                cutoff = self.low_cutoff / nyquist
                b, a = butter(self.filter_order, cutoff, btype='high')
                
            elif self.filter_type == 'bandpass':
                # Band-pass filter
                low_cutoff = self.low_cutoff / nyquist
                high_cutoff = self.high_cutoff / nyquist
                b, a = butter(self.filter_order, [low_cutoff, high_cutoff], btype='band')
                
            else:
                logger.warning(f"Unsupported filter type: {self.filter_type}")
                return audio_data
            
            # Apply filter (use filtfilt for zero-phase filtering)
            filtered_audio = filtfilt(b, a, audio_data)
            
            return filtered_audio
            
        except Exception as e:
            logger.error(f"Error in audio filtering: {e}")
            return audio_data
    
    def remove_silence(self, audio_data, sample_rate):
        """Remove silence from audio data.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Audio data with silence removed
        """
        logger.debug("Removing silence")
        
        try:
            # Convert threshold to amplitude
            amplitude_threshold = self.silence_threshold
            
            # Calculate frame size in samples
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.010 * sample_rate)    # 10ms hop
            
            # Calculate energy of frames
            energy = librosa.feature.rms(
                y=audio_data,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Find frames above threshold
            voiced_frames = energy > amplitude_threshold
            
            # Convert frame-level decisions to sample-level mask
            mask = np.repeat(voiced_frames, hop_length)
            
            # Ensure mask is same length as audio
            if len(mask) < len(audio_data):
                mask = np.pad(mask, (0, len(audio_data) - len(mask)))
            else:
                mask = mask[:len(audio_data)]
            
            # Apply mask to remove silence
            audio_without_silence = audio_data[mask]
            
            # If too much is removed, return original
            if len(audio_without_silence) < len(audio_data) * 0.1:
                logger.warning("Too much audio removed as silence, returning original")
                return audio_data
            
            return audio_without_silence
            
        except Exception as e:
            logger.error(f"Error in silence removal: {e}")
            return audio_data
    
    def enhance_signal(self, audio_data, sample_rate):
        """Enhance speech signal using selected method.
        
        Args:
            audio_data (numpy.ndarray): Audio data as numpy array
            sample_rate (int): Sample rate of audio data
            
        Returns:
            numpy.ndarray: Enhanced audio data
        """
        logger.debug(f"Enhancing signal using {self.enhancement_method}")
        
        try:
            if self.enhancement_method == 'spectral_subtraction':
                # Simple spectral subtraction
                # Convert to frequency domain
                stft = librosa.stft(audio_data)
                
                # Estimate noise from first 0.5 seconds (assumed to be noise)
                noise_frames = int(0.5 * sample_rate / librosa.stft.win_length)
                noise_stft = stft[:, :noise_frames]
                noise_mag = np.mean(np.abs(noise_stft), axis=1, keepdims=True)
                
                # Apply spectral subtraction
                stft_mag = np.abs(stft)
                stft_phase = np.angle(stft)
                enhanced_mag = np.maximum(stft_mag - noise_mag, 0)
                
                # Convert back to time domain
                enhanced_stft = enhanced_mag * np.exp(1j * stft_phase)
                enhanced_audio = librosa.istft(enhanced_stft)
                
                return enhanced_audio
                
            elif self.enhancement_method == 'wiener':
                # Wiener filtering
                from scipy.signal import wiener
                enhanced_audio = wiener(audio_data)
                return enhanced_audio
                
            else:
                logger.warning(f"Unsupported enhancement method: {self.enhancement_method}")
                return audio_data
                
        except Exception as e:
            logger.error(f"Error in signal enhancement: {e}")
            return audio_data


# Example usage
if __name__ == "__main__":
    import soundfile as sf
    import matplotlib.pyplot as plt
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample configuration
    config = {
        'audio': {
            'preprocessing': {
                'noise_reduction_enabled': True,
                'noise_reduction_strength': 0.5,
                'stationary': True,
                'normalization_enabled': True,
                'target_db': -20,
                'filtering_enabled': True,
                'filter_type': 'bandpass',
                'low_cutoff': 80,
                'high_cutoff': 7500,
                'filter_order': 4,
                'silence_removal_enabled': True,
                'silence_threshold': 0.03,
                'min_silence_duration': 0.3,
                'enhancement_enabled': False
            }
        }
    }
    
    # Create audio preprocessor
    preprocessor = AudioPreprocessor(config)
    
    # Load test audio file
    try:
        audio_file = "test_audio.wav"
        audio_data, sample_rate = librosa.load(audio_file, sr=None)
        
        # Process audio
        processed_audio, _ = preprocessor.process(audio_data, sample_rate)
        
        # Save processed audio
        sf.write("processed_audio.wav", processed_audio, sample_rate)
        
        # Plot before and after
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 1, 1)
        plt.title("Original Audio")
        plt.plot(audio_data)
        
        plt.subplot(2, 1, 2)
        plt.title("Processed Audio")
        plt.plot(processed_audio)
        
        plt.tight_layout()
        plt.savefig("audio_comparison.png")
        plt.close()
        
        print("Audio processed and saved to processed_audio.wav")
        print("Comparison plot saved to audio_comparison.png")
        
    except Exception as e:
        print(f"Error in example: {e}")
