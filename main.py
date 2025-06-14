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
import time
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the Python path
sys.path.append('.')

from modules.asr_module import ASRModule, ASRConfig
from modules.tts_module import TTSModule, TTSConfig
from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def live_demo(voice_mode=True):
    """
    Starts an interactive, real-time demo of the voicebot.
    
    Args:
        voice_mode: If True, use voice input/output. If False, use text input/output.
    """
    logging.info(f"Starting live demo (voice_mode={voice_mode})...")

    # 1. Initialize modules
    try:
        logging.info("Loading configuration...")
        nlp_config = NLPConfig.from_yaml()
        asr_config = ASRConfig.from_yaml()
        tts_config = TTSConfig.from_yaml()
        
        logging.info("Initializing NLP Pipeline...")
        nlp_pipeline = NLPPipeline(config=nlp_config)
        
        logging.info("Initializing Response Generator...")
        response_generator = ResponseGenerator()
        
        if voice_mode:
            logging.info("Initializing ASR Module...")
            asr_module = ASRModule(config=asr_config)
            
            logging.info("Initializing TTS Module...")
            tts_module = TTSModule(config=tts_config)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to initialize modules: {e}")
        print(f"Error: Could not start the demo. Details: {e}")
        return

    # 2. Start interactive loop
    print("\n--- P2P Lending Voicebot Demo ---")
    print("Ask me anything about Peer-to-Peer lending.")
    if voice_mode:
        print("Speak to interact, or say 'exit' to end the session.")
        print("Type 'text' to switch to text mode.")
    else:
        print("Type your questions, or 'exit' to end the session.")
        print("Type 'voice' to switch to voice mode.")
    print()
    
    session_id = "live-demo-session"
    conversation_history = [] # List to store the conversation turns
    
    # Welcome message
    welcome_message = "Hello! I'm your P2P Lending Assistant. How can I help you today?"
    print(f"Bot: {welcome_message}")
    if voice_mode:
        tts_module.speak(welcome_message)
    
    current_mode = "voice" if voice_mode else "text"

    while True:
        try:
            if current_mode == "voice":
                print("\n[Listening...] (Say something or type 'text' to switch modes)")
                user_query = asr_module.listen_and_transcribe(duration=5.0)
                print(f"You said: {user_query}")
            else:
                user_query = input("You: ")
                
            # Handle mode switching
            if current_mode == "voice" and user_query.lower() == "text":
                current_mode = "text"
                switch_msg = "Switching to text input mode."
                print(f"Bot: {switch_msg}")
                continue
            elif current_mode == "text" and user_query.lower() == "voice":
                current_mode = "voice"
                switch_msg = "Switching to voice input mode."
                print(f"Bot: {switch_msg}")
                continue
                
            # Handle exit commands
            if user_query.lower() in ["exit", "quit"]:
                goodbye_msg = "Goodbye! Thank you for using our P2P Lending Assistant."
                print(f"Bot: {goodbye_msg}")
                if current_mode == "voice":
                    tts_module.speak(goodbye_msg)
                break
            
            if not user_query.strip():
                continue

            # Append user message to history
            conversation_history.append({"role": "user", "content": user_query})

            # The pipeline now needs the full history
            nlp_data = nlp_pipeline.process_input(
                user_query, 
                session_id=session_id,
                history=conversation_history
            )
            
            # Step 2: Generate the final response
            final_response = response_generator.get_final_answer(nlp_data)

            # Append bot message to history
            conversation_history.append({"role": "assistant", "content": final_response})
            
            print(f"Bot: {final_response}")
            
            # If in voice mode, speak the response
            if current_mode == "voice":
                tts_module.speak(final_response)

        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during the demo loop: {e}", exc_info=True)
            error_msg = "I'm sorry, an unexpected error occurred. Please try again."
            print(f"Bot: {error_msg}")
            if current_mode == "voice":
                try:
                    tts_module.speak(error_msg)
                except:
                    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the P2P Lending Voice AI Assistant demo.")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["text", "voice"],
        default="voice", 
        help="The mode to run the demo in: 'text' for text-only or 'voice' for voice interaction."
    )
    
    args = parser.parse_args()
    voice_mode = args.mode == "voice"
    
    live_demo(voice_mode=voice_mode)