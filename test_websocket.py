#!/usr/bin/env python3
"""
Test script for the WebSocket client.
"""

import asyncio
import json
import os
from modules.websocket_client import WebSocketClient

async def test_websocket():
    """Test the WebSocket client by sending a message."""
    
    # Create WebSocket client with the API Gateway URL
    ws_url = "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/"
    client = WebSocketClient(base_url=ws_url)
    
    try:
        # Send a test message
        message = {
            "text": "Hello, who are you?"
        }
        
        print(f"Sending message: {json.dumps(message, indent=2)}")
        response = await client.send_message(message)
        
        if response:
            print("Response received:")
            print(json.dumps(response, indent=2))
        else:
            print("No response received or an error occurred.")
    
    except Exception as e:
        print(f"Error during test: {e}")
    
    finally:
        # Close the connection
        await client.close()
        print("Connection closed.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_websocket()) 