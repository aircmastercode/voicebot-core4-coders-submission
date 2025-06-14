# Logic for generating or retrieving responses. 

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Extracts the final user-facing response from the backend's JSON output.
    """
    def __init__(self):
        """Initializes the ResponseGenerator."""
        logger.info("ResponseGenerator initialized.")

    def get_final_answer(self, nlp_data: Optional[Dict[str, Any]]) -> str:
        """
        Parses the NLP data to find the final response text.

        Args:
            nlp_data: The full JSON response from the backend.

        Returns:
            A user-facing string response, or a fallback message.
        """
        if not nlp_data:
            logger.warning("NLP data is empty. Returning a fallback response.")
            return "I'm sorry, I'm having trouble understanding. Could you please rephrase?"

        # Check for error responses from the API
        if "statusCode" in nlp_data and nlp_data["statusCode"] != 200:
            if "body" in nlp_data and isinstance(nlp_data["body"], str):
                try:
                    body_data = json.loads(nlp_data["body"])
                    if "error" in body_data:
                        logger.error(f"Backend API error: {body_data['error']}")
                        return f"I'm sorry, I'm experiencing a technical issue. {body_data.get('error_description', 'Please try again later.')}"
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse error body: {nlp_data['body']}")
            
            return "I'm sorry, I'm experiencing a technical issue right now. Please try again later."

        # The backend response might have the final answer in a 'response' key
        # or it could be nested inside a JSON string in the 'body'.
        
        if "response" in nlp_data:
            return nlp_data["response"]
            
        if "body" in nlp_data and isinstance(nlp_data["body"], str):
            try:
                body_data = json.loads(nlp_data["body"])
                if "response" in body_data:
                    return body_data["response"]
                elif "error" in body_data:
                    logger.error(f"Error in body: {body_data['error']}")
                    return f"I'm sorry, I'm experiencing a technical issue. {body_data.get('error_description', 'Please try again later.')}"
            except json.JSONDecodeError:
                logger.error("Failed to parse the 'body' string as JSON.")
                
        logger.warning("Could not find a 'response' key in the backend output.")
        return "I found some information, but I'm having trouble formulating a response. Please try asking in a different way."

# Example usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Re-using the same config loader for simplicity
        generator = ResponseGenerator()

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
        final_answer = generator.get_final_answer(sample_nlp_data)
        
        print("\n--- Final Generated Answer ---")
        print(final_answer)
        print("----------------------------\n")

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize ResponseGenerator: {e}") 