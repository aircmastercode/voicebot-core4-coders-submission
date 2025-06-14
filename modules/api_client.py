"""
API Client for connecting to AWS Lambda and API Gateway.
This module provides a client to interact with the P2P Lending Voice AI Assistant backend.
"""

import json
import requests
import logging
import os
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    """A client for making requests to the NLP API Gateway."""

    def __init__(self, base_url: str, api_key: str):
        if not base_url:
            raise ValueError("API base_url cannot be empty.")
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
        logger.info(f"APIClient initialized for base URL: {self.base_url}")

    def post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Sends a POST request to a specified endpoint.

        Args:
            endpoint: The API endpoint to send the request to (e.g., '/nlp').
            data: The JSON payload to send.

        Returns:
            The JSON response from the API, or None if an error occurs.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"A request error occurred: {req_err}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in APIClient: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Get API Gateway URL and key from environment variables
    api_gateway_url = os.environ.get('API_GATEWAY_URL', '')
    api_gateway_key = os.environ.get('API_GATEWAY_KEY', '')
    
    if not api_gateway_url:
        logger.error("API_GATEWAY_URL environment variable not set")
        exit(1)
        
    api_client = APIClient(
        base_url=api_gateway_url,
        api_key=api_gateway_key
    )
    
    # Test intent recognition
    intent_result = api_client.post('/nlp', {'operation': 'recognize_intent', 'text': 'How do I invest in P2P lending?'})
    print(f"Intent: {json.dumps(intent_result, indent=2)}")
    
    # Test knowledge base query
    kb_result = api_client.post('/nlp', {'operation': 'query_knowledge_base', 'query': 'What are the regulations for P2P lending in India?', 'max_results': 3})
    print(f"Knowledge Base Results: {json.dumps(kb_result, indent=2)}")
