#!/usr/bin/env python3
"""
Test script for P2P Lending Voice Assistant API integration.
This script tests the connection to the API Gateway and Lambda function.
"""

import os
import json
from modules.api_client import P2PLendingAPIClient

def main():
    # Get API Gateway URL and key from environment variables
    api_gateway_url = os.environ.get('API_GATEWAY_URL')
    api_gateway_key = os.environ.get('API_GATEWAY_KEY')
    
    if not api_gateway_url:
        print("ERROR: API_GATEWAY_URL environment variable not set")
        print("Please set it to your API Gateway URL")
        print("Example: export API_GATEWAY_URL='https://abc123def.execute-api.region.amazonaws.com/dev'")
        return
    
    print(f"Connecting to API Gateway: {api_gateway_url}")
    
    # Initialize the API client
    api_client = P2PLendingAPIClient(
        api_base_url=api_gateway_url,
        api_key=api_gateway_key
    )
    
    # Test query to the knowledge base
    print("\n1. Testing knowledge base query...")
    query = "What are the regulations for P2P lending in India?"
    print(f"Query: {query}")
    
    try:
        result = api_client.query_knowledge_base(query)
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test response generation
    print("\n2. Testing response generation...")
    query = "How do I invest in P2P lending?"
    print(f"Query: {query}")
    
    try:
        result = api_client.generate_response(query)
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
