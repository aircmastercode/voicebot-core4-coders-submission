#!/usr/bin/env python3
"""
Test script for the P2P Lending NLP Pipeline integration with AWS Bedrock.
This script tests the complete NLP pipeline flow from intent recognition to response generation.
"""

import os
import json
import logging
from modules.nlp_pipeline import BedrockNLPProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Initialize the NLP processor
    processor = BedrockNLPProcessor()
    logger.info("Initialized NLP Processor")
    
    # Test queries for different intents
    test_queries = [
        "What are the current interest rates for P2P lending in India?",
        "How do I invest 50,000 rupees in P2P lending?",
        "What are the risks associated with P2P lending?",
        "Tell me about the regulations for P2P lending platforms",
        "Compare LenDenClub and Faircent platforms"
    ]
    
    # Process each test query through the complete NLP pipeline
    for i, query in enumerate(test_queries):
        print(f"\n=== Test Query {i+1}: '{query}' ===\n")
        
        try:
            # Step 1: Intent Recognition
            logger.info(f"Recognizing intent for: {query}")
            intent_data = processor.recognize_intent(query)
            print(f"Recognized Intent: {intent_data.get('intent', 'unknown')}")
            print(f"Confidence: {intent_data.get('confidence', 0)}")
            
            # Step 2: Entity Extraction
            logger.info(f"Extracting entities from: {query}")
            entities = processor.extract_entities(query, intent=intent_data.get('intent'))
            print(f"Extracted Entities: {json.dumps(entities, indent=2)}")
            
            # Step 3: Generate Response
            logger.info(f"Generating response for: {query}")
            response = processor.generate_response(
                user_input=query,
                intent_data=intent_data,
                session_id=f"test-session-{i}"
            )
            print(f"Generated Response: {response}")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            print(f"Error: {str(e)}")
    
    print("\nNLP Pipeline test completed")

if __name__ == "__main__":
    # Check if API Gateway URL is set
    if not os.environ.get('API_GATEWAY_URL'):
        print("API_GATEWAY_URL environment variable not set")
        print("Please set the API_GATEWAY_URL environment variable:")
        print("export API_GATEWAY_URL='https://your-api-id.execute-api.us-west-2.amazonaws.com/dev'")
    else:
        main()
