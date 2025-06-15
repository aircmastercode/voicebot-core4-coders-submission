#!/usr/bin/env python3
"""
Test script for the ASR (Automatic Speech Recognition) module.
This script transcribes an audio file to text using the ASR module.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append('.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_asr(file_path):
    """
    Test the ASR module by transcribing an audio file.
    
    Args:
        file_path: Path to the audio file to transcribe.
    """
    try:
        from modules.asr_module import ASRModule, ASRConfig
        
        logger.info(f"Testing ASR with file: {file_path}")
        
        # Initialize ASR module
        asr_config = ASRConfig.from_yaml()
        asr_module = ASRModule(config=asr_config)
        
        # Transcribe the file
        transcription = asr_module.transcribe_file(file_path)
        
        logger.info(f"Transcription: {transcription}")
        print(f"\nTranscription result: {transcription}\n")
        
        return transcription
    except Exception as e:
        logger.error(f"Error testing ASR: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the ASR module with an audio file")
    parser.add_argument("file", help="Path to an audio file to transcribe")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
        
    test_asr(args.file) 