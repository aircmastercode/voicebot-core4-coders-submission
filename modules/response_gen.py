# Logic for generating or retrieving responses. 

import logging
from typing import Dict, Any, Optional

from modules.api_client import APIClient
from modules.nlp_pipeline import NLPConfig  # Re-using the config loader

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Generates a final, user-facing response by calling the backend's 
    'generate_response' operation with relevant context.
    """
    def __init__(self, config: NLPConfig):
        """Initializes the ResponseGenerator with an API client."""
        self.api_client = APIClient(base_url=config.api_base_url, api_key=config.api_key)
        self.api_endpoint = config.api_nlp_endpoint
        logger.info("ResponseGenerator initialized.")

    def generate_response(self, user_query: str, nlp_data: Optional[Dict[str, Any]]) -> str:
        """
        Generates a polished response using the 'generate_response' API operation.

        Args:
            user_query: The original query from the user.
            nlp_data: The structured output from the NLPPipeline.

        Returns:
            A final, user-facing string response from the backend.
        """
        if not nlp_data:
            logger.warning("NLP data is empty. Returning a fallback response.")
            return "I'm sorry, I'm having trouble understanding. Could you please rephrase?"

        # --- Default Fallback Response ---
        fallback_response = "That's a great question. While I don't have a specific answer right now, I am always learning. Is there anything else I can help with?"

        intent = nlp_data.get("intent", "unknown_intent")
        if intent == "GREETING":
            return "Hello! How can I help you learn about P2P lending today?"

        # --- Prepare for 'generate_response' API call ---
        knowledge_results = nlp_data.get("knowledge_results", [])
        if not knowledge_results:
            logger.info("No knowledge base results found. Returning fallback.")
            return fallback_response

        # Combine the content from the knowledge base to create the context
        context = " ".join(
            filter(None, [result.get("content", "") for result in knowledge_results])
        )

        if not context.strip():
            logger.info("Knowledge base content was empty. Returning fallback.")
            return fallback_response

        # Build the payload exactly as specified in the screenshot
        payload = {
            "operation": "generate_response",
            "text": user_query,
            "context": context,
            "session_id": nlp_data.get("session_id", "default-session")
        }

        logger.info(f"Calling 'generate_response' operation for query: '{user_query[:50]}...'")
        
        # Call the API to get the final, generated response
        api_response = self.api_client.post(self.api_endpoint, payload)

        if api_response and "response" in api_response:
            final_response = api_response["response"]
            logger.info(f"Successfully received final response from backend.")
            return final_response
        else:
            logger.error("Failed to get a valid 'generate_response' from the backend.")
            return fallback_response

# Example usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Re-using the same config loader for simplicity
        config = NLPConfig.from_yaml()
        generator = ResponseGenerator(config=config)

        # The user's original question
        user_query = "What are the risks of P2P lending?"

        # This data would normally come from the NLPPipeline
        sample_nlp_data = {
            "intent": "QUERY_RISKS",
            "entities": [{"type": "topic", "value": "P2P lending"}],
            "knowledge_results": [
                {"content": "Peer-to-peer (P2P) lending carries risks such as borrower default."},
                {"content": "Another risk is platform risk, where the P2P platform itself could fail."}
            ],
            "session_id": "test-session-12"
        }

        # Generate the final response
        final_answer = generator.generate_response(user_query, sample_nlp_data)
        
        print("\n--- Final Generated Answer ---")
        print(final_answer)
        print("----------------------------\n")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize ResponseGenerator: {e}") 