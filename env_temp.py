#!/usr/bin/env python3
"""
Temporary environment variables setup for testing.
This script sets placeholder environment variables for testing the application.
"""

import os

# Set AWS Configuration placeholders
os.environ["API_GATEWAY_URL"] = "https://example.execute-api.us-west-2.amazonaws.com/dev"
os.environ["API_GATEWAY_KEY"] = "placeholder-api-key"

# Set OpenAI API Key placeholder
os.environ["OPENAI_API_KEY"] = "sk-placeholder"

# Set AWS Bedrock Configuration placeholders
os.environ["KNOWLEDGE_BASE_ID"] = "placeholder-knowledge-base-id"
os.environ["S3_BUCKET_NAME"] = "placeholder-bucket"

print("Environment variables set for testing.") 