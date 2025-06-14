#!/usr/bin/env python3
"""
Test script for querying about loan options.
"""

import asyncio
import json
from modules.websocket_client import WebSocketClient

async def test_loan_options():
    """Test the WebSocket client by sending a query about loan options."""
    
    # Create WebSocket client with the API Gateway URL
    ws_url = "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/"
    client = WebSocketClient(base_url=ws_url)
    
    try:
        # Define a stream handler function
        def handle_stream(chunk):
            if "response_chunk" in chunk:
                print(f"Chunk: {chunk['response_chunk']}", end="", flush=True)
            elif "response" in chunk:
                print(f"Complete: {chunk['response']}")
            elif "error" in chunk:
                print(f"Error: {chunk['error']}")
        
        # Send a test message with streaming
        message = {
            "text": "What loan options are available for me?"
        }
        
        print(f"Sending message: {json.dumps(message, indent=2)}")
        await client.send_message(message, stream_handler=handle_stream)
        
        # Wait a bit to receive all chunks
        await asyncio.sleep(10)
    
    except Exception as e:
        print(f"Error during test: {e}")
    
    finally:
        # Close the connection
        await client.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_loan_options()) 