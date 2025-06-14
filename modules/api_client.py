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

class P2PLendingAPIClient:
    """
    Client for interacting with P2P Lending Voice AI Assistant API Gateway endpoints.
    This client handles communication with the Lambda-backed API for NLP operations.
    """
    
    def __init__(self, api_base_url: str, api_key: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            api_base_url: Base URL for the API Gateway endpoint
            api_key: Optional API key for authentication
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        if api_key:
            self.headers['x-api-key'] = api_key
    
    def _make_request(self, endpoint: str, method: str = 'POST', data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the API Gateway.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            data: Request payload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.api_base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            else:
                response = requests.post(url, headers=self.headers, json=data)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            # Return error information that can be handled by the caller
            return {
                'error': True,
                'message': str(e),
                'status_code': getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            }
    
    def recognize_intent(self, text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Recognize user intent from text.
        
        Args:
            text: User input text
            session_id: Optional session ID for conversation context
            
        Returns:
            Dictionary containing intent information
        """
        payload = {
            'operation': 'recognize_intent',
            'text': text,
            'session_id': session_id
        }
        
        return self._make_request('nlp', method='POST', data=payload)
    
    def extract_entities(self, text: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract entities from user text.
        
        Args:
            text: User input text
            intent: Optional recognized intent to improve entity extraction
            
        Returns:
            Dictionary containing extracted entities
        """
        payload = {
            'operation': 'extract_entities',
            'text': text,
            'intent': intent
        }
        
        return self._make_request('nlp', method='POST', data=payload)
    
    def query_knowledge_base(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Query the P2P lending knowledge base.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing knowledge base results
        """
        payload = {
            'operation': 'query_knowledge_base',
            'query': query,
            'max_results': max_results
        }
        
        return self._make_request('nlp', method='POST', data=payload)
    
    def generate_response(self, 
                         query: str, 
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         knowledge_items: Optional[List[str]] = None,
                         session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response using the Bedrock foundation model.
        
        Args:
            query: User query
            conversation_history: Optional list of conversation history
            knowledge_items: Optional list of knowledge items to include
            session_id: Optional session ID
            
        Returns:
            Dictionary containing the generated response
        """
        # Format the payload exactly as shown in the screenshot
        payload = {
            "operation": "generate_response",
            "text": "What are the risks of P2P lending?",
            "context": "Add the context here.",
            "session_id": "test-session-123"
        }
        
        # Override with actual query and session
        payload["text"] = query
        if session_id:
            payload["session_id"] = session_id
            
        # Add context from knowledge base if available
        if knowledge_items and len(knowledge_items) > 0:
            payload["context"] = "\n\n".join(knowledge_items)
        
        return self._make_request('nlp', method='POST', data=payload)
    
    def process_voice_input(self, audio_data: bytes, language_code: str = 'en-US') -> Dict[str, Any]:
        """
        Process voice input through the API.
        
        Args:
            audio_data: Binary audio data
            language_code: Language code for speech recognition
            
        Returns:
            Dictionary containing processed text and detected language
        """
        # For voice data, we need to use different headers
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/octet-stream'
        
        url = f"{self.api_base_url}/speech"
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                data=audio_data,
                params={'language_code': language_code}
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Voice processing request failed: {str(e)}")
            return {
                'error': True,
                'message': str(e),
                'status_code': getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            }


# Example usage
if __name__ == "__main__":
    # Get API Gateway URL and key from environment variables
    api_gateway_url = os.environ.get('API_GATEWAY_URL', '')
    api_gateway_key = os.environ.get('API_GATEWAY_KEY', '')
    
    if not api_gateway_url:
        logger.error("API_GATEWAY_URL environment variable not set")
        exit(1)
        
    api_client = P2PLendingAPIClient(
        api_base_url=api_gateway_url,
        api_key=api_gateway_key
    )
    
    # Test intent recognition
    intent_result = api_client.recognize_intent("How do I invest in P2P lending?")
    print(f"Intent: {json.dumps(intent_result, indent=2)}")
    
    # Test knowledge base query
    kb_result = api_client.query_knowledge_base("What are the regulations for P2P lending in India?")
    print(f"Knowledge Base Results: {json.dumps(kb_result, indent=2)}")
