# Logic for Natural Language Processing (intent, entities, etc.) using AWS Bedrock.

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple

# Import API client
from modules.api_client import P2PLendingAPIClient

# Import our AWS configuration
from config.aws_config import get_aws_config

logger = logging.getLogger(__name__)

class BedrockNLPProcessor:
    """Main class for handling NLP tasks using AWS Bedrock.
    
    This class provides a unified interface for intent recognition, entity extraction,
    and knowledge retrieval using AWS Bedrock services. It leverages Bedrock agents
    for understanding user queries about P2P lending.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Bedrock NLP processor with API client and configuration.
        """
        # Get AWS configuration
        aws_config = get_aws_config()
        api_config = aws_config.get('api_gateway', {
            'base_url': os.getenv('API_GATEWAY_URL', 'https://your-api-id.execute-api.us-west-2.amazonaws.com/dev'),
            'api_key': os.getenv('API_GATEWAY_KEY', '')
        })
        
        # Initialize API client
        self.api_client = P2PLendingAPIClient(
            api_base_url=api_config.get('base_url'),
            api_key=api_config.get('api_key')
        )
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize session storage
        self.sessions = {}
        
        logger.info(f"Initialized Bedrock NLP Processor")

    def _get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get an existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Session ID string
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                'history': [],
                'context': {}
            }
        return session_id
    
    def _add_to_session_history(self, session_id: str, message: Dict[str, str]) -> None:
        """Add a message to the session history.
        
        Args:
            session_id: Session ID
            message: Message dictionary with 'role' and 'content' keys
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {'history': []}
        
        self.sessions[session_id]['history'].append(message)
    
    def recognize_intent(self, text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Recognize user intent from text using the API Gateway.
        
        Args:
            text: User input text
            session_id: Optional session ID for conversation context
            
        Returns:
            Dictionary containing intent information and confidence
        """
        session_id = self._get_or_create_session(session_id)
        
        # Store user input in session history
        self._add_to_session_history(session_id, {'role': 'user', 'content': text})
        
        try:
            # Call the API Gateway endpoint for intent recognition
            self.logger.info(f"Calling API for intent recognition: {text[:50]}...")
            response = self.api_client.recognize_intent(text, session_id)
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return {
                    'intent': 'OTHER',
                    'confidence': 0.3,
                    'error': response.get('message'),
                    'session_id': session_id
                }
                
            # Extract intent from API response
            intent = response.get('intent', 'OTHER')
            confidence = response.get('confidence', 0.7)
            
            # Add response to session history
            self._add_to_session_history(session_id, {'role': 'assistant', 'content': f"Intent: {intent}"})
            
            return {
                'intent': intent,
                'confidence': confidence,
                'raw_response': response.get('raw_response', ''),
                'session_id': session_id,
                'entities': response.get('entities', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error in intent recognition: {str(e)}")
            return {
                'intent': 'OTHER',
                'confidence': 0.3,
                'error': str(e),
                'session_id': session_id,
                'entities': {}
            }
    
    def extract_entities(self, user_input: str, intent: str = None) -> Dict[str, Any]:
        """Extract entities from user input using Bedrock.
        
        Args:
            user_input: The user's query text
            intent: Optional intent to guide entity extraction
            
        Returns:
            Dictionary of extracted entities
        """
        # For P2P lending, we're interested in entities like:
        # - Currency amounts
        # - Time periods (loan duration)
        try:
            # Call the API Gateway endpoint for entity extraction
            self.logger.info(f"Calling API for entity extraction: {text[:50]}...")
            response = self.api_client.extract_entities(text, intent)
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return {}
            
            # Return the extracted entities
            return response.get('entities', {})
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
            return {}
    
    def query_knowledge_base(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Query the knowledge base through API Gateway.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of knowledge base results
        """
        try:
            # Call the API Gateway endpoint for knowledge base queries
            self.logger.info(f"Calling API for knowledge base query: {query[:50]}...")
            response = self.api_client.query_knowledge_base(query, max_results)
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return []
            
            # Return the knowledge base results
            return response.get('results', [])
            
        except Exception as e:
            self.logger.error(f"Error querying knowledge base: {str(e)}")
            return []
    
    def generate_response(self, user_input: str, intent_data: Dict[str, Any], 
                         session_id: Optional[str] = None) -> str:
        """Generate a response using API Gateway and Lambda.
        
        Args:
            user_input: The user's query text
            intent_data: Intent and entity information
            session_id: Optional session ID for conversation context
            
        Returns:
            Generated response text
        """
        session_id = self._get_or_create_session(session_id)
        
        # Get conversation history from session
        history = self.sessions.get(session_id, {}).get('history', [])
        
        try:
            # Call the API Gateway endpoint for response generation
            self.logger.info(f"Calling API for response generation: {user_input[:50]}...")
            
            # First query knowledge base for context
            kb_results = self.query_knowledge_base(user_input)
            
            # Then generate response using the API client
            response = self.api_client.generate_response(
                text=user_input,
                intent=intent_data.get('intent', 'general_inquiry'),
                entities=intent_data.get('entities', {}),
                knowledge_results=kb_results,
                session_id=session_id
            )
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return "I'm sorry, I'm having trouble generating a response right now. Please try again later."
            
            # Get the generated response text
            response_text = response.get('response', "I'm sorry, I'm having trouble generating a response right now.")
            
            # Add response to session history
            self._add_to_session_history(session_id, {'role': 'assistant', 'content': response_text})
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I'm having trouble generating a response right now. Please try again later."


# Example usage
if __name__ == "__main__":
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Initialize processor with default AWS workshop configuration
    processor = BedrockNLPProcessor()
    
    # Log the configuration being used
    logger.info(f"Using AWS region: {processor.region_name}")
    logger.info(f"Using Bedrock model: {processor.foundation_model_id}")
    
    try:
        # Test intent recognition
        logger.info("Testing intent recognition...")
        result = processor.recognize_intent("What are the current interest rates for P2P lending?")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Entities: {result['entities']}")
        
        # Test entity extraction
        logger.info("Testing entity extraction...")
        entities = processor.extract_entities("I want to invest 50,000 rupees for 6 months at 12% interest rate")
        print(f"Extracted entities: {entities}")
        
        # Test knowledge base query if configured
        if processor.knowledge_base_id:
            logger.info("Testing knowledge base query...")
            kb_results = processor.query_knowledge_base("P2P lending regulations in India")
            for result in kb_results:
                print(f"Source: {result['source']}")
                print(f"Text: {result['text'][:100]}...")
                print(f"Relevance: {result['relevance_score']}")
                print("---")
        else:
            logger.warning("Knowledge base ID not configured, skipping knowledge base test")
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        print("To use this module, you need to configure Bedrock resources in the AWS console")
        print("or update the config/aws_config.py file with your resource IDs.")