#!/usr/bin/env python3
"""
P2P Lending Awareness & Sales AI Assistant

Main entry point for the chat assistant application.
This script initializes the WebSocket client and starts the interactive chat interface.
"""

import os
import sys
import logging
import asyncio
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append('.')

from modules.websocket_client import WebSocketClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# WebSocket endpoint
WEBSOCKET_URL = "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/"

async def chat_demo():
    """
    Starts an interactive, real-time chat demo with the P2P Lending Assistant.
    Uses WebSocket for communication with the backend.
    """
    logging.info("Starting chat demo...")

    # Initialize WebSocket client
    try:
        client = WebSocketClient(base_url=WEBSOCKET_URL)
        connected = await client.connect()
        if not connected:
            logging.error("Failed to connect to WebSocket server")
            print("Error: Could not connect to the chat server. Please try again later.")
            return
    except Exception as e:
        logging.error(f"Failed to initialize WebSocket client: {e}")
        print(f"Error: Could not start the demo. Details: {e}")
        return

    # Start interactive loop
    print("\n--- P2P Lending Chat Assistant Demo ---")
    print("Ask me anything about Peer-to-Peer lending.")
    print("Type 'exit' to end the session.")
    print()
    
    # Welcome message
    print("Bot: Hello! I'm your P2P Lending Assistant. How can I help you today?")
    
    # Define a stream handler function to display responses
    def handle_stream(chunk):
        if "response_chunk" in chunk:
            # For streaming responses, print each chunk without newline
            print(chunk["response_chunk"], end="", flush=True)
        elif "response" in chunk:
            # For complete responses, print with newline
            if "response_chunk" not in chunk:  # Only print if not already printed as chunks
                print(f"Bot: {chunk['response']}")
        elif "error" in chunk:
            print(f"Error: {chunk['error']}")

    while True:
        try:
            # Get user input
            user_query = input("\nYou: ")
            
            # Handle exit command
            if user_query.lower() in ["exit", "quit"]:
                print("Bot: Goodbye! Thank you for using our P2P Lending Assistant.")
                break
            
            if not user_query.strip():
                continue

            # Send message to WebSocket server
            message = {
                "text": user_query,
                "action": "sendMessage"
            }
            
            print("Bot: ", end="", flush=True)  # Start the bot's response line
            
            # Send the message and handle streaming response
            session_id = await client.send_message(message, stream_handler=handle_stream)
            
            if not session_id:
                print("\nError: Failed to get a response from the server.")

        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"\nBot: I'm sorry, an unexpected error occurred. Please try again.")

    # Close the WebSocket connection
    await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(chat_demo())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        logging.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"Error: {e}")