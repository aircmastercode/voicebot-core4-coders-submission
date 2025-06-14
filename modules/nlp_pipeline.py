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
            'base_url': os.getenv('API_GATEWAY_URL', 'https://your-api-id.execute-api.us-west-2.amazonaws.com/dev/nlp'),
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
        try:
            # Call the API Gateway endpoint for entity extraction
            self.logger.info(f"Calling API for entity extraction: {user_input[:50]}...")
            
            # Use the API client to extract entities
            response = self.api_client.extract_entities(text=user_input, intent=intent)
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return {}
            
            # Parse the response body if it's a string (JSON)
            if 'body' in response and isinstance(response['body'], str):
                try:
                    response_data = json.loads(response['body'])
                    entities = response_data.get('entities', {})
                    return entities
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse entity extraction response as JSON")
                    return {}
            
            # If the response already contains entities directly
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
            
            # Debug: Log the raw response structure
            self.logger.info(f"Knowledge base response type: {type(response)}, keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
            
            # Check for errors in the API response
            if response.get('error'):
                self.logger.error(f"API error: {response.get('message')}")
                return []
            
            # Parse the response body if it's a string (JSON)
            if 'body' in response and isinstance(response['body'], str):
                try:
                    self.logger.info(f"Parsing response body: {response['body'][:200]}...")
                    response_data = json.loads(response['body'])
                    self.logger.info(f"Parsed response data keys: {list(response_data.keys())}")
                    
                    if 'results' in response_data:
                        self.logger.info(f"Found results: {response_data['results'][:2]}")
                        return response_data['results']
                    else:
                        self.logger.warning(f"No 'results' key found in knowledge base response. Keys: {list(response_data.keys())}")
                        return []
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse knowledge base response as JSON: {str(e)}")
                    return []
            
            # If the response already contains results directly
            return response.get('results', [])
            
        except Exception as e:
            self.logger.error(f"Error querying knowledge base: {str(e)}")
            return []
    
    def generate_response(self, user_input: str, intent_data: Dict[str, Any], 
                         session_id: Optional[str] = None) -> str:
        """Generate a response using API Gateway and Lambda with hybrid knowledge base + LLM approach.
        
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
            self.logger.info("Querying knowledge base for relevant context...")
            kb_results = self.query_knowledge_base(user_input)
            
            # Extract content from knowledge base results
            knowledge_context = []
            if kb_results and isinstance(kb_results, list):
                self.logger.info(f"Found {len(kb_results)} relevant knowledge base items")
                for result in kb_results:
                    if 'content' in result and result['content']:
                        # Add source attribution to the content
                        source = result.get('source', 'Unknown')
                        content = result.get('content', '')
                        knowledge_context.append(f"{content}\n(Source: {source})")
            else:
                self.logger.info("No relevant knowledge base items found")
            
            # Then generate response using the API client with knowledge context
            self.logger.info("Generating response with knowledge context...")
            response = self.api_client.generate_response(
                query=user_input,
                knowledge_items=knowledge_context,
                conversation_history=history,
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
    
    # Log the API Gateway configuration being used
    api_config = get_aws_config().get('api_gateway', {})
    logger.info(f"Using API Gateway URL: {api_config.get('base_url', 'Not configured')}")
    logger.info(f"Using API Gateway stage: {api_config.get('stage', 'dev')}")
    logger.info(f"API Key configured: {'Yes' if api_config.get('api_key') else 'No'}")
    logger.info(f"AWS region: {get_aws_config().get('aws', {}).get('region_name', 'us-west-2')}")
    
    try:
        # Test intent recognition
        logger.info("Testing intent recognition...")
        result = processor.recognize_intent("What are the current interest rates for P2P lending?")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']}")
        if 'entities' in result:
            print(f"Entities: {result['entities']}")
        else:
            print("No entities in result")
        
        # Test entity extraction
        logger.info("Testing entity extraction...")
        entities = processor.extract_entities("I want to invest 50,000 rupees for 6 months at 12% interest rate")
        print(f"Extracted entities: {entities}")
        
        # Test knowledge base query
        logger.info("Testing knowledge base query...")
        kb_results = processor.query_knowledge_base("P2P lending regulations in India")
        
        if kb_results and isinstance(kb_results, list):
            logger.info(f"Found {len(kb_results)} knowledge base results")
            for result in kb_results:
                print(f"Source: {result.get('source', 'Unknown')}")
                print(f"Content: {result.get('content', '')[:100]}...")
                print(f"Score: {result.get('score', 0)}")
                print("---")
        else:
            print("No knowledge base results returned or invalid format.")
            logger.warning(f"KB results type: {type(kb_results)}, value: {kb_results}")
            
        # Test hybrid response generation
        logger.info("\n\nTesting hybrid response generation...")
        print("\nUser query: What are the regulations for P2P lending in India?")
        
        # Get intent data
        intent_data = processor.recognize_intent("What are the regulations for P2P lending in India?")
        
        # Generate response with hybrid approach
        response = processor.generate_response(
            user_input="What are the regulations for P2P lending in India?",
            intent_data=intent_data,
            session_id="test-session-123"
        )
        
        print("\nGenerated response:")
        print(f"{response}\n")
        print("---"*20)
            
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        print("To use this module, you need to configure the API Gateway URL and API key")
        print("in your .env file or update the config/aws_config.py file with your API Gateway settings.")
        print(f"Error details: {str(e)}")