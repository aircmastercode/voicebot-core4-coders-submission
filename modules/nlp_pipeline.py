# This file is ready for the new NLP Pipeline implementation. 

import os
import yaml
import logging
import json
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from modules.websocket_client import WebSocketClient

# Initialize logging
logger = logging.getLogger(__name__)

@dataclass
class NLPConfig:
    """Configuration for the NLP Pipeline, loaded from config.yaml."""
    api_base_url: str
    api_key: str
    api_nlp_endpoint: str

    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> "NLPConfig":
        """Loads configuration from a YAML file and environment variables."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {config_path}")
            raise

        # Fetch API Gateway details from environment variables for security
        api_base_url = os.getenv("API_GATEWAY_URL", config.get("api_gateway", {}).get("base_url"))
        api_key = os.getenv("API_GATEWAY_KEY", config.get("api_gateway", {}).get("api_key"))
        
        if not api_base_url:
            raise ValueError("API_GATEWAY_URL is not set in environment or config.yaml.")

        return cls(
            api_base_url=api_base_url,
            api_key=api_key,
            api_nlp_endpoint=config.get("api_gateway", {}).get("endpoints", {}).get("nlp", "/nlp")
        )

class NLPPipeline:
    """
    Orchestrates NLP processing by sending requests to the backend API via WebSocket.
    """
    def __init__(self, config: NLPConfig, tts_service=None):
        self.config = config
        self.tts_service = tts_service
        self.ws_client = WebSocketClient(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key,
            tts_service=self.tts_service
        )
        logger.info("NLP Pipeline initialized successfully.")
        
    async def process_input(self, text: str, session_id: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None, 
                      stream_handler: Optional[Callable[[Dict[str, Any]], None]] = None) -> Optional[Dict[str, Any]]:
        """
        Processes user input by calling the backend NLP service via WebSocket.

        Args:
            text: The user's input text.
            session_id: An optional session ID for maintaining context.
            history: An optional list of previous conversation history.
            stream_handler: Optional callback function to handle streaming responses.

        Returns:
            A dictionary with the structured NLP output from the backend,
            or None if an error occurred.
        """
        if not text:
            logger.warning("Input text is empty. Skipping processing.")
            return None

        # Payload for the WebSocket client, only containing the text.
        payload = {
            "text": text
        }

        logger.info(f"Sending text to NLP backend with payload: {json.dumps(payload, indent=2)}")
        
        # Await the async WebSocket call directly
        response = await self.ws_client.send_message(payload, stream_handler=stream_handler)
            
        if response and not stream_handler:
            logger.info(f"Raw response from backend: {json.dumps(response, indent=2)}")
            logger.info("Successfully received NLP processing results from backend.")
            
            # This part is for the web server, not run_inference
            if "response" in response and self.tts_service and "audio_url" not in response:
                try:
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = f"static/audio/{audio_filename}"
                    audio_file = self.tts_service.text_to_speech(response["response"], audio_path)
                    if audio_file:
                        response["audio_url"] = f"/static/audio/{audio_filename}"
                        logger.info(f"Generated audio for response: {response['audio_url']}")
                except Exception as e:
                    logger.error(f"Error generating audio for response: {e}")
            
            return response
        elif stream_handler:
            # For streaming, the ws_client returns the session_id
            return {"session_id": response} if response else None
        else:
            logger.error("Failed to get a response from the NLP backend.")
            return None
    
    async def close(self):
        """Gracefully closes the WebSocket connection."""
        try:
            await self.ws_client.close()
            logger.info("NLP Pipeline resources cleaned up successfully.")
        except Exception as e:
            logger.error(f"Error during NLP pipeline cleanup: {e}")

# Example usage:
if __name__ == '__main__':
    # This is for demonstration purposes. 
    # In the actual application, the pipeline would be initialized once.
    logging.basicConfig(level=logging.INFO)
    
    # Ensure you have a config.yaml and your .env file is set up
    # with API_GATEWAY_URL and API_GATEWAY_KEY for this to work.
    try:
        nlp_config = NLPConfig.from_yaml()
        pipeline = NLPPipeline(config=nlp_config)
        
        # Example of processing user input with streaming
        def handle_stream(chunk):
            if "response_chunk" in chunk:
                print(f"Chunk: {chunk['response_chunk']}")
            elif "response" in chunk:
                print(f"Complete: {chunk['response']}")
            elif "error" in chunk:
                print(f"Error: {chunk['error']}")
        
        user_query = "Hi, what are the risks of peer-to-peer lending?"
        result = pipeline.process_input(user_query, session_id="test-session-123", stream_handler=handle_stream)
        print(f"Result: {result}")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize NLP pipeline: {e}") 