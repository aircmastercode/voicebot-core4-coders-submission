# This file is ready for the new NLP Pipeline implementation. 

import os
import yaml
import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from modules.api_client import APIClient

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
    Orchestrates NLP processing by sending requests to the backend API.
    """
    def __init__(self, config: NLPConfig):
        self.config = config
        self.api_client = APIClient(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key
        )
        logger.info("NLP Pipeline initialized successfully.")

    def process_input(self, text: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Processes user input by calling the backend NLP service.

        This single method sends the user's text to the API Gateway,
        which then routes it to a Lambda function. The Lambda is responsible for
        the full NLP workflow: intent recognition, entity extraction, and 
        knowledge base retrieval.

        Args:
            text: The user's input text.
            session_id: An optional session ID for maintaining context.

        Returns:
            A dictionary with the structured NLP output from the backend,
            or None if an error occurred.
        """
        if not text:
            logger.warning("Input text is empty. Skipping processing.")
            return None

        payload = {
            "operation": "generate_response",
            "text": text,
            "session_id": session_id
        }

        logger.info(f"Sending text to NLP backend with payload: {json.dumps(payload, indent=2)}")
        response = self.api_client.post(self.config.api_nlp_endpoint, payload)

        if response:
            logger.info(f"Raw response from backend: {json.dumps(response, indent=2)}")
            logger.info("Successfully received NLP processing results from backend.")
            return response
        else:
            logger.error("Failed to get a response from the NLP backend.")
            return None

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
        
        # Example of processing user input
        user_query = "Hi, what are the risks of peer-to-peer lending?"
        nlp_result = pipeline.process_input(user_query, session_id="test-session-123")

        if nlp_result:
            print("\n--- NLP Result ---")
            print(json.dumps(nlp_result, indent=2))
            print("------------------\n")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize NLP pipeline: {e}") 