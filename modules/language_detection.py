#!/usr/bin/env python3
"""
Language Detection Module for P2P Lending Voice AI Assistant.

This module provides language detection functionality for the ASR module,
enabling automatic language switching between English, Hindi, and Hinglish.
"""

import re
import logging
import numpy as np
from collections import Counter
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for deterministic language detection
DetectorFactory.seed = 0

# Setup logging
logger = logging.getLogger(__name__)


class LanguageDetector:
    """Language detection for multilingual support."""
    
    def __init__(self, config):
        """Initialize the language detector with configuration.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.lang_config = config.get('languages', {})
        
        # Language settings
        self.default_language = self.lang_config.get('default', 'en')
        self.supported_languages = self.lang_config.get('supported', ['en', 'hi'])
        
        # Hinglish detection settings
        self.hinglish_threshold = self.lang_config.get('hinglish_threshold', 0.3)
        
        # Language detection history for context-aware detection
        self.detection_history = []
        self.history_size = self.lang_config.get('detection_history_size', 5)
        
        # Common Hindi and English words for Hinglish detection
        self.hindi_markers = set([
            'hai', 'ki', 'kya', 'aur', 'ka', 'ko', 'se', 'me', 'mein', 'hain',
            'par', 'ye', 'yeh', 'woh', 'jo', 'na', 'ne', 'ke', 'hi', 'to', 'tha',
            'thi', 'ho', 'jaa', 'kar', 'raha', 'rahi', 'kuch', 'nahi', 'nahin',
            'apna', 'apne', 'unka', 'unke', 'iska', 'iske', 'uska', 'uske'
        ])
        
        logger.info("Language detector initialized")
    
    def detect_language(self, text):
        """Detect language of the given text.
        
        Args:
            text (str): Text to detect language from
            
        Returns:
            str: Detected language code ('en', 'hi', 'hi-en')
        """
        if not text or not text.strip():
            return self.default_language
        
        text = text.lower()
        
        try:
            # First check for Hinglish (mixed Hindi-English)
            if self._is_hinglish(text):
                detected_lang = 'hi-en'  # Hinglish code
            else:
                # Use langdetect for standard language detection
                detected_lang = detect(text)
                
                # Map to supported languages
                if detected_lang == 'hi':
                    detected_lang = 'hi'
                else:
                    # Default to English for any other language
                    detected_lang = 'en'
            
            # Update detection history
            self._update_history(detected_lang)
            
            # Apply context-aware correction
            final_lang = self._context_aware_detection(detected_lang)
            
            logger.debug(f"Detected language: {final_lang} (initial: {detected_lang})")
            return final_lang
            
        except LangDetectException as e:
            logger.warning(f"Language detection error: {e}")
            return self.default_language
    
    def _is_hinglish(self, text):
        """Detect if text is Hinglish (mixed Hindi-English).
        
        Args:
            text (str): Text to analyze
            
        Returns:
            bool: True if text is likely Hinglish
        """
        # Tokenize into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return False
        
        # Count Hindi marker words
        hindi_word_count = sum(1 for word in words if word in self.hindi_markers)
        
        # Calculate ratio of Hindi marker words
        hindi_ratio = hindi_word_count / len(words)
        
        # Check for Roman Hindi words with English words
        has_roman_hindi = hindi_ratio > 0
        has_english = any(word.isascii() for word in words)
        
        # Classify as Hinglish if it has both Hindi markers and English words
        # but not enough Hindi markers to be pure Hindi
        is_hinglish = (has_roman_hindi and has_english and 
                      hindi_ratio >= self.hinglish_threshold and 
                      hindi_ratio < 0.7)
        
        return is_hinglish
    
    def _update_history(self, lang_code):
        """Update language detection history.
        
        Args:
            lang_code (str): Detected language code
        """
        self.detection_history.append(lang_code)
        
        # Keep history at specified size
        if len(self.detection_history) > self.history_size:
            self.detection_history.pop(0)
    
    def _context_aware_detection(self, current_lang):
        """Apply context-aware correction to language detection.
        
        Args:
            current_lang (str): Currently detected language
            
        Returns:
            str: Possibly corrected language code
        """
        # If history is too short, return current detection
        if len(self.detection_history) < 3:
            return current_lang
        
        # Count languages in history
        lang_counts = Counter(self.detection_history)
        
        # Get most common language in history
        most_common_lang = lang_counts.most_common(1)[0][0]
        
        # If current detection differs from history trend, apply correction
        # based on confidence threshold
        if current_lang != most_common_lang:
            history_confidence = lang_counts[most_common_lang] / len(self.detection_history)
            
            # If history strongly suggests a different language, override current detection
            if history_confidence > 0.7:  # High confidence threshold
                logger.debug(f"Correcting language from {current_lang} to {most_common_lang} based on context")
                return most_common_lang
        
        return current_lang


# Example usage
if __name__ == "__main__":
    import yaml
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sample configuration
    config = {
        'languages': {
            'default': 'en',
            'supported': ['en', 'hi', 'hi-en'],
            'hinglish_threshold': 0.3,
            'detection_history_size': 5
        }
    }
    
    # Create language detector
    detector = LanguageDetector(config)
    
    # Test with different texts
    test_texts = [
        "Hello, how are you doing today?",
        "नमस्ते, आप कैसे हैं?",
        "Main aaj market mein shopping karne jaa raha hoon",
        "I want to invest in P2P lending",
        "Mujhe P2P lending mein invest karna hai"
    ]
    
    for text in test_texts:
        lang = detector.detect_language(text)
        print(f"Text: {text}\nDetected language: {lang}\n")
