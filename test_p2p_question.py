#!/usr/bin/env python3
"""
Test script for asking a P2P lending specific question via WebSocket.
"""

import asyncio
import json
import os
from modules.websocket_client import WebSocketClient

async def test_p2p_question():
    """Test the WebSocket client by sending a P2P lending question."""
    
    # Create WebSocket client with the API Gateway URL
    ws_url = "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/"
    client = WebSocketClient(base_url=ws_url)
    
    try:
        # Send a P2P lending specific question
        message = {
            "text": "What are the risks associated with P2P lending in India?"
        }
        
        print(f"Sending question: {json.dumps(message, indent=2)}")
        response = await client.send_message(message)
        
        if response:
            print("Response received:")
            print(json.dumps(response, indent=2))
            
            # If we got a session_id, let's ask a follow-up question
            if "session_id" in response:
                session_id = response["session_id"]
                follow_up = {
                    "text": "How can I mitigate these risks?",
                    "session_id": session_id
                }
                
                print("\nSending follow-up question:")
                print(json.dumps(follow_up, indent=2))
                
                follow_up_response = await client.send_message(follow_up)
                if follow_up_response:
                    print("Follow-up response received:")
                    print(json.dumps(follow_up_response, indent=2))
                else:
                    print("No follow-up response received.")
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
    asyncio.run(test_p2p_question()) 