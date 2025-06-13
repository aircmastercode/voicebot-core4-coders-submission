#!/usr/bin/env python3
"""
P2P Lending Awareness & Sales Voice AI Assistant

Main entry point for the voice assistant application.
This script initializes all components and starts the interactive voice interface.
"""

import os
import sys
import argparse
import yaml
import logging
from dotenv import load_dotenv
from pathlib import Path

# Import modules
try:
    from modules.asr_module import ASR
    from modules.nlp_pipeline import NLPPipeline
    from modules.response_gen import ResponseGenerator
    from modules.utils import setup_logger, load_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed all dependencies with 'pip install -r requirements.txt'")
    sys.exit(1)

# Setup logging
logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Main Voice Assistant class that coordinates all components."""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize the Voice Assistant with configuration.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Setup logging
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', 'logs/app.log')
        setup_logger(log_level, log_file)
        
        logger.info("Initializing P2P Lending Voice AI Assistant")
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize all assistant components."""
        try:
            # Initialize ASR module
            logger.info("Initializing ASR module")
            self.asr = ASR(self.config)
            
            # Initialize NLP Pipeline
            logger.info("Initializing NLP Pipeline")
            self.nlp = NLPPipeline(self.config)
            
            # Initialize Response Generator
            logger.info("Initializing Response Generator")
            self.response_gen = ResponseGenerator(self.config)
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def start_interactive(self):
        """Start the interactive voice assistant."""
        logger.info("Starting interactive mode")
        print("\n" + "="*50)
        print("P2P Lending Voice AI Assistant - Interactive Mode")
        print("Speak or type 'exit' to quit")
        print("="*50 + "\n")
        
        try:
            # Start the conversation loop
            self._conversation_loop()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            # Cleanup resources
            self._cleanup()
    
    def _conversation_loop(self):
        """Main conversation loop for the assistant."""
        context = {}
        conversation_active = True
        
        # Welcome message
        welcome_response = self.response_gen.generate_response(
            "Welcome to P2P Lending Assistant", 
            intent="greeting",
            entities={},
            context=context
        )
        print(f"Assistant: {welcome_response}")
        
        while conversation_active:
            # Get user input (either voice or text for debugging)
            if self.config.get('application', {}).get('debug_mode', False):
                # Text input in debug mode
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    conversation_active = False
                    continue
            else:
                # Voice input in normal mode
                print("Listening...")
                user_input = self.asr.transcribe()
                print(f"You: {user_input}")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    conversation_active = False
                    continue
            
            # Process through NLP pipeline
            nlp_result = self.nlp.process(user_input, context)
            
            # Generate response
            response = self.response_gen.generate_response(
                user_input,
                intent=nlp_result['intent'],
                entities=nlp_result['entities'],
                context=nlp_result['context']
            )
            
            # Update context
            context = nlp_result['context']
            
            # Output response
            print(f"Assistant: {response}")
    
    def _cleanup(self):
        """Clean up resources before exiting."""
        logger.info("Cleaning up resources")
        # Add any cleanup code here (close connections, etc.)


def main():
    """Main function to parse arguments and start the assistant."""
    parser = argparse.ArgumentParser(description="P2P Lending Voice AI Assistant")
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode (text input instead of voice)"
    )
    
    args = parser.parse_args()
    
    try:
        # Create assistant instance
        assistant = VoiceAssistant(config_path=args.config)
        
        # Start interactive mode
        assistant.start_interactive()
    except Exception as e:
        logger.error(f"Error running assistant: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()