#!/usr/bin/env python3
"""
Test script for directly testing the hybrid response generation API.
"""

import json
import requests
import os
from dotenv import load_dotenv
from config.aws_config import get_aws_config

# Load environment variables
load_dotenv()

# Get API Gateway configuration
aws_config = get_aws_config()
api_config = aws_config.get('api_gateway', {})

# API Gateway URL
api_base_url = api_config.get('base_url')
api_stage = api_config.get('stage', 'dev')
api_key = api_config.get('api_key')

# Debug API config
print(f"API Config: {api_config}")

if not api_base_url:
    print("Error: API Gateway URL not configured")
    exit(1)

# Construct full URL - ensure stage is included correctly
if '/dev' in api_base_url or api_base_url.endswith('/dev'):
    # Stage already in URL
    url = f"{api_base_url}/nlp"
else:
    # Add stage to URL
    url = f"{api_base_url}/{api_stage}/nlp"

# Headers
headers = {
    'Content-Type': 'application/json'
}

# Always add API key if available
if api_key:
    headers['x-api-key'] = api_key
    print(f"Using API key: {api_key[:5]}...")
else:
    print("WARNING: No API key found in configuration")
    
    # Try to get API key from environment variable directly
    env_api_key = os.environ.get('API_GATEWAY_KEY')
    if env_api_key:
        headers['x-api-key'] = env_api_key
        print(f"Using API key from environment: {env_api_key[:5]}...")
    else:
        print("WARNING: No API_GATEWAY_KEY found in environment variables")

# Test payload exactly as specified
payload = {
    "operation": "generate_response",
    "text": "What are the risks of P2P lending?",
    "context": "Add the context here",
    "session_id": "test-session-12"
}

# Make the request
print(f"Sending request to {url}")
print(f"Headers: {headers}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=payload)
    
    # Print response status and headers
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    # Print response body
    try:
        response_json = response.json()
        print(f"Response Body: {json.dumps(response_json, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response Body (raw): {response.text}")
        
except Exception as e:
    print(f"Error: {str(e)}")
