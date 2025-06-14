"""
AWS Configuration for P2P Lending Voice AI Assistant.
This file contains configuration for AWS services including Bedrock.
"""

import os
from dotenv import load_dotenv

# Import Bedrock resource IDs
from config.bedrock_resources import get_bedrock_resources

# Load environment variables from .env file if it exists
load_dotenv()

def get_aws_config():
    """
    Get AWS configuration for the application.
    
    Uses the default AWS credential provider chain, which will automatically
    use credentials from environment variables, AWS config file, or EC2/ECS
    instance profiles.
    
    Returns:
        Dict containing AWS configuration
    """
    
    return {
        # AWS credentials and region
        'aws': {
            'region_name': os.getenv('AWS_REGION', 'us-west-2')
        },
        
        # Bedrock resources
        'bedrock': get_bedrock_resources(),
        
        # S3 configuration
        's3': {
            'bucket_name': os.getenv('S3_BUCKET_NAME', ''),
            'knowledge_base_prefix': os.getenv('S3_KB_PREFIX', 'knowledge-base/')
        },
        
        # API Gateway configuration for Lambda integration
        'api_gateway': {
            'base_url': os.getenv('API_GATEWAY_URL', ''),
            'api_key': os.getenv('API_GATEWAY_KEY', ''),
            'stage': os.getenv('API_GATEWAY_STAGE', 'dev')
        },
        
        'app': {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'cache_ttl': int(os.getenv('CACHE_TTL', '3600'))
        }
    }

# Workshop-specific configuration
WORKSHOP_CONFIG = {
    'team_name': os.getenv('TEAM_NAME', 'Core4 Coders'),
    'team_code': os.getenv('TEAM_CODE', '98e7-15c8f0-56'),
    'workshop_url': os.getenv('WORKSHOP_URL', 'https://catalog.us-east-1.prod.workshops.aws/join?access-code=98e7-15c8f0-56')
}

def get_aws_config():
    """
    Returns the AWS configuration dictionary.
    """
    return AWS_CONFIG

def get_workshop_config():
    """
    Returns the workshop-specific configuration.
    """
    return WORKSHOP_CONFIG
