"""
WebSocket Client for connecting to AWS API Gateway WebSocket API.
This module provides a client to interact with the P2P Lending Voice AI Assistant backend via WebSockets.
"""

import json
import logging
import os
import asyncio
import websockets
import re
import uuid
from typing import Dict, Any, Optional, List, Callable, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketClient:
    """A client for making WebSocket connections to the API Gateway."""

    def __init__(self, base_url: str, api_key: str = None, tts_service=None):
        if not base_url:
            raise ValueError("API base_url cannot be empty.")
        self.base_url = base_url
        self.api_key = api_key
        self.connection = None
        self.tts_service = tts_service  # TTS service for generating audio
        logger.info(f"WebSocketClient initialized for base URL: {self.base_url}")

    async def connect(self):
        """Establishes a WebSocket connection to the API Gateway."""
        try:
            # The websockets library doesn't support extra_headers in connect
            # Instead, we'll add the API key as a query parameter if needed
            connect_url = self.base_url
            if self.api_key:
                if "?" in connect_url:
                    connect_url += f"&api-key={self.api_key}"
                else:
                    connect_url += f"?api-key={self.api_key}"
            
            self.connection = await websockets.connect(connect_url)
            logger.info("WebSocket connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            return False

    def _chunk_text(self, text: str, chunk_size: int = 10) -> List[str]:
        """
        Break down a large text into smaller chunks for smoother streaming.
        
        Args:
            text: The text to chunk
            chunk_size: Approximate number of words per chunk
            
        Returns:
            List of text chunks
        """
        # Split by lines first to maintain coherence
        lines = text.split('\n')
        chunks = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Add empty lines as separate chunks to preserve formatting
                chunks.append("")
                continue
                
            # If the line is very long, split it by sentences
            if len(line.split()) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', line)
                for sentence in sentences:
                    if sentence.strip():
                        chunks.append(sentence.strip())
            else:
                # Add the line as a single chunk
                chunks.append(line)
        
        return chunks

    async def send_message(self, message: Dict[str, Any], stream_handler: Optional[Callable[[Dict[str, Any]], None]] = None) -> Optional[Union[Dict[str, Any], str]]:
        """
        Sends a message over the WebSocket connection.

        Args:
            message: The message payload to send.
            stream_handler: Optional callback function to handle streaming responses.

        Returns:
            The response from the server, or None if an error occurs.
            If stream_handler is provided, returns the session_id instead.
        """
        if not self.connection:
            connected = await self.connect()
            if not connected:
                return None
        
        try:
            # Format the message according to the required structure
            formatted_message = {
                "action": "sendMessage",
                "text": message.get("text", "")
            }
            
            # Include other parameters if they exist
            if "session_id" in message:
                formatted_message["session_id"] = message["session_id"]
            if "history" in message:
                formatted_message["history"] = message["history"]
                
            await self.connection.send(json.dumps(formatted_message))
            
            # If stream_handler is provided, handle streaming responses
            if stream_handler:
                session_id = None
                accumulated_response = ""
                last_chunk = False
                
                # Keep receiving messages until we get a complete response or error
                while True:
                    response_data = await self.connection.recv()
                    response = json.loads(response_data)
                    
                    # Save session ID if available
                    if "session_id" in response and not session_id:
                        session_id = response["session_id"]
                    
                    # If this is a response chunk, break it down into smaller chunks
                    if "response_chunk" in response:
                        chunk_text = response["response_chunk"]
                        accumulated_response += chunk_text
                        
                        # Break down large chunks into line-by-line pieces for deliberate streaming
                        smaller_chunks = self._chunk_text(chunk_text)
                        for i, small_chunk in enumerate(smaller_chunks):
                            # Create a new response object for each smaller chunk
                            small_response = {
                                "response_chunk": small_chunk + "\n",  # Add newline to ensure line breaks
                            }
                            if session_id:
                                small_response["session_id"] = session_id
                            
                            # Call the stream handler with the smaller chunk
                            stream_handler(small_response)
                            
                            # Add a 1-second delay between chunks for a more deliberate line-by-line display
                            if i < len(smaller_chunks) - 1:
                                await asyncio.sleep(1.0)  # 1-second delay between lines
                    else:
                        # For complete responses or errors, pass them through as is
                        
                        # If this is a complete response, use the accumulated response if we have it
                        if "response" in response:
                            # If we've been accumulating streaming chunks and this is the final response,
                            # use the accumulated text as the complete response
                            if accumulated_response and not last_chunk:
                                response["response"] = accumulated_response
                                last_chunk = True
                            
                            # If we have TTS service available, generate audio for the complete response
                            if self.tts_service:
                                try:
                                    # Generate a unique filename
                                    audio_filename = f"{uuid.uuid4()}.mp3"
                                    audio_path = f"static/audio/{audio_filename}"
                                    
                                    # Convert response to speech
                                    audio_file = self.tts_service.text_to_speech(response["response"], audio_path)
                                    
                                    # Add audio URL to the response
                                    if audio_file:
                                        response["audio_url"] = f"/static/audio/{audio_filename}"
                                        logger.info(f"Generated audio for WebSocket response: {response['audio_url']}")
                                except Exception as e:
                                    logger.error(f"Error generating audio for WebSocket response: {e}")
                        
                        # Pass the response to the stream handler
                        stream_handler(response)
                    
                    # If this is a complete response or error, break the loop
                    if "response" in response or "error" in response:
                        break
                
                # Return the session ID
                return session_id
            else:
                # For non-streaming mode, just get a single response
                response = await self.connection.recv()
                response_data = json.loads(response)
                
                # Generate audio if applicable
                if "response" in response_data and self.tts_service:
                    try:
                        # Generate a unique filename
                        audio_filename = f"{uuid.uuid4()}.mp3"
                        audio_path = f"static/audio/{audio_filename}"
                        
                        # Convert response to speech
                        audio_file = self.tts_service.text_to_speech(response_data["response"], audio_path)
                        
                        # Add audio URL to the response
                        if audio_file:
                            response_data["audio_url"] = f"/static/audio/{audio_filename}"
                            logger.info(f"Generated audio for WebSocket response: {response_data['audio_url']}")
                    except Exception as e:
                        logger.error(f"Error generating audio for WebSocket response: {e}")
                
                return response_data
        except Exception as e:
            logger.error(f"Error sending message over WebSocket: {e}")
            return None

    async def close(self):
        """Closes the WebSocket connection."""
        if self.connection:
            await self.connection.close()
            logger.info("WebSocket connection closed")

# Example usage
async def example_usage():
    # Get API Gateway URL and key from environment variables
    api_gateway_url = os.environ.get('API_GATEWAY_URL', '')
    api_gateway_key = os.environ.get('API_GATEWAY_KEY', '')
    
    if not api_gateway_url:
        logger.error("API_GATEWAY_URL environment variable not set")
        return
        
    client = WebSocketClient(
        base_url=api_gateway_url,
        api_key=api_gateway_key
    )
    
    # Define a stream handler function
    def handle_stream(chunk):
        if "response_chunk" in chunk:
            print(f"Received chunk: {chunk['response_chunk']}")
        elif "response" in chunk:
            print(f"Received complete response: {chunk['response']}")
        elif "error" in chunk:
            print(f"Received error: {chunk['error']}")
    
    # Send a test message with streaming
    session_id = await client.send_message({
        "text": "How do I invest in P2P lending?"
    }, stream_handler=handle_stream)
    
    print(f"Session ID: {session_id}")
    
    # Close the connection
    await client.close()

if __name__ == "__main__":
    asyncio.run(example_usage()) 