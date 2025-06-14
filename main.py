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

# Add the project root to the Python path
sys.path.append('.')

from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def live_demo():
    """
    Starts an interactive, real-time demo of the voicebot.
    """
    logging.info("Starting live demo...")

    # 1. Initialize modules
    try:
        logging.info("Loading configuration...")
        config = NLPConfig.from_yaml()
        
        logging.info("Initializing NLP Pipeline...")
        nlp_pipeline = NLPPipeline(config=config)
        
        logging.info("Initializing Response Generator...")
        response_generator = ResponseGenerator(config=config)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to initialize modules: {e}")
        print(f"Error: Could not start the demo. Details: {e}")
        return

    # 2. Start interactive loop
    print("\n--- P2P Lending Voicebot Demo ---")
    print("Ask me anything about Peer-to-Peer lending.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    session_id = "live-demo-session" # A consistent session ID for the demo

    while True:
        try:
            user_query = input("You: ")
            if user_query.lower() in ["exit", "quit"]:
                print("Bot: Goodbye!")
                break
            
            if not user_query.strip():
                continue

            # Step 1: Process input through the NLP pipeline
            nlp_data = nlp_pipeline.process_input(user_query, session_id=session_id)
            
            # Step 2: Generate the final response
            final_response = response_generator.generate_response(user_query, nlp_data)
            
            print(f"Bot: {final_response}")

        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during the demo loop: {e}", exc_info=True)
            print("Bot: I'm sorry, an unexpected error occurred. Please try again.")

if __name__ == "__main__":
    live_demo()