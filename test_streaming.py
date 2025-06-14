#!/usr/bin/env python3
"""
Test script for the WebSocket streaming functionality.
"""

import asyncio
import json
import os
from modules.websocket_client import WebSocketClient

async def test_streaming():
    """Test the WebSocket client with streaming responses."""
    
    # Create WebSocket client with the API Gateway URL
    ws_url = "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/"
    client = WebSocketClient(base_url=ws_url)
    
    try:
        # Define a stream handler function
        def handle_stream(chunk):
            if "response_chunk" in chunk:
                print(f"Chunk: {chunk['response_chunk']}")
            elif "response" in chunk:
                print(f"Complete: {chunk['response']}")
            elif "error" in chunk:
                print(f"Error: {chunk['error']}")
            
            # Print the session ID if available
            if "session_id" in chunk:
                print(f"Session ID: {chunk['session_id']}")
        
        # Send a test message with streaming
        message = {
            "text": "What are the risks associated with P2P lending in India?"
        }
        
        print(f"Sending message: {json.dumps(message, indent=2)}")
        session_id = await client.send_message(message, stream_handler=handle_stream)
        
        if session_id:
            print(f"\nFinal session ID: {session_id}")
            
            # Send a follow-up question with the same session ID
            follow_up = {
                "text": "How can I mitigate these risks?",
                "session_id": session_id
            }
            
            print(f"\nSending follow-up: {json.dumps(follow_up, indent=2)}")
            await client.send_message(follow_up, stream_handler=handle_stream)
        else:
            print("No session ID received.")
    
    except Exception as e:
        print(f"Error during test: {e}")
    
    finally:
        # Close the connection
        await client.close()
        print("Connection closed.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_streaming()) 