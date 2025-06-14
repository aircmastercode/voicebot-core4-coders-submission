#!/usr/bin/env python3
"""
Test script for the P2P Lending API client with AWS Bedrock integration.
This script tests the API client's ability to communicate with the Lambda function
through API Gateway and interact with AWS Bedrock services.
"""

import os
import json
import logging
from modules.api_client import P2PLendingAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Get API Gateway URL from environment variables
    api_gateway_url = os.environ.get('API_GATEWAY_URL')
    api_gateway_key = os.environ.get('API_GATEWAY_KEY', '')
    
    if not api_gateway_url:
        logger.error("API_GATEWAY_URL environment variable not set")
        print("Please set the API_GATEWAY_URL environment variable:")
        print("export API_GATEWAY_URL='https://9kti499scf.execute-api.us-west-2.amazonaws.com/dev'")
        return
    
    logger.info(f"Using API Gateway URL: {api_gateway_url}")
    
    # Initialize the API client
    api_client = P2PLendingAPIClient(
        api_base_url=api_gateway_url,
        api_key=api_gateway_key
    )
    
    # Test generate_response operation
    print("\n=== Testing Response Generation ===")
    query = "What are P2P lending regulations in India?"
    context = "P2P lending in India is regulated by RBI. The RBI has issued guidelines for NBFC-P2P."
    
    try:
        response = api_client.generate_response(
            query=query,
            knowledge_items=[context],
            session_id="test-session-123"
        )
        
        print(f"Query: {query}")
        print(f"Context: {context}")
        print("\nResponse:")
        if 'error' in response:
            print(f"Error: {response['message']}")
        else:
            print(json.dumps(response, indent=2))
    except Exception as e:
        logger.error(f"Error during response generation: {str(e)}")
    
    # Test knowledge base query operation
    print("\n=== Testing Knowledge Base Query ===")
    query = "What are the risks of P2P lending?"
    
    try:
        response = api_client.query_knowledge_base(query=query)
        
        print(f"Query: {query}")
        print("\nResponse:")
        if 'error' in response:
            print(f"Error: {response['message']}")
        else:
            print(json.dumps(response, indent=2))
    except Exception as e:
        logger.error(f"Error during knowledge base query: {str(e)}")
    
    # Test combined approach (query knowledge base then generate response)
    print("\n=== Testing Combined Knowledge Base + Response Generation ===")
    query = "How do I invest in P2P lending?"
    
    try:
        # First query the knowledge base
        kb_response = api_client.query_knowledge_base(query=query)
        
        # Parse the nested JSON response
        context = ""
        if 'body' in kb_response and isinstance(kb_response['body'], str):
            try:
                # Parse the inner JSON string
                kb_data = json.loads(kb_response['body'])
                
                # Extract content from results
                if 'results' in kb_data and isinstance(kb_data['results'], list):
                    for result in kb_data['results']:
                        if isinstance(result, dict) and 'content' in result:
                            context += result['content'] + "\n\n"
            except json.JSONDecodeError:
                logger.error("Failed to parse knowledge base response body as JSON")
        
        # If we got context, generate a response
        if context:
            response = api_client.generate_response(
                query=query,
                knowledge_items=[context],
                session_id="test-session-456"
            )
            
            print(f"Query: {query}")
            print(f"Context from KB (excerpt): {context[:200]}...")
            print("\nGenerated Response:")
            
            # Parse the response which might also be nested
            if 'error' in response:
                print(f"Error: {response['message']}")
            elif 'body' in response and isinstance(response['body'], str):
                try:
                    response_data = json.loads(response['body'])
                    print(json.dumps(response_data, indent=2))
                except json.JSONDecodeError:
                    print(response['body'])
            else:
                print(json.dumps(response, indent=2))
        else:
            print("No context retrieved from knowledge base")
    except Exception as e:
        logger.error(f"Error during combined operation: {str(e)}")

if __name__ == "__main__":
    main()
