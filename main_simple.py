#!/usr/bin/env python3
"""
P2P Lending Awareness & Sales Voice AI Assistant

Simplified main entry point for the voice assistant application.
This version only uses text mode and doesn't import ASR/TTS modules.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the Python path
sys.path.append('.')

from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def text_mode_demo():
    """
    Starts an interactive, text-only demo of the voicebot.
    """
    logging.info("Starting text-mode demo...")

    # 1. Initialize modules
    try:
        logging.info("Loading configuration...")
        nlp_config = NLPConfig.from_yaml()
        
        logging.info("Initializing NLP Pipeline...")
        nlp_pipeline = NLPPipeline(config=nlp_config)
        
        logging.info("Initializing Response Generator...")
        response_generator = ResponseGenerator()
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to initialize modules: {e}")
        print(f"Error: Could not start the demo. Details: {e}")
        return

    # 2. Start interactive loop
    print("\n--- P2P Lending Voicebot Demo (Text-only Mode) ---")
    print("Ask me anything about Peer-to-Peer lending.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    session_id = "text-demo-session"
    conversation_history = [] # List to store the conversation turns
    
    # Welcome message
    welcome_message = "Hello! I'm your P2P Lending Assistant. How can I help you today?"
    print(f"Bot: {welcome_message}")

    while True:
        try:
            user_query = input("You: ")
                
            # Handle exit commands
            if user_query.lower() in ["exit", "quit"]:
                goodbye_msg = "Goodbye! Thank you for using our P2P Lending Assistant."
                print(f"Bot: {goodbye_msg}")
                break
            
            if not user_query.strip():
                continue

            # Append user message to history
            conversation_history.append({"role": "user", "content": user_query})

            # Process the query
            nlp_data = nlp_pipeline.process_input(
                user_query, 
                session_id=session_id,
                history=conversation_history
            )
            
            # Generate the final response
            final_response = response_generator.get_final_answer(nlp_data)

            # Append bot message to history
            conversation_history.append({"role": "assistant", "content": final_response})
            
            print(f"Bot: {final_response}")

        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during the demo loop: {e}", exc_info=True)
            error_msg = "I'm sorry, an unexpected error occurred. Please try again."
            print(f"Bot: {error_msg}")

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    text_mode_demo() 