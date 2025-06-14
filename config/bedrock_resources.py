"""
Bedrock resource configuration for P2P Lending Voice AI Assistant.
This file contains the resource IDs for AWS Bedrock services.
"""

# Bedrock Agent Configuration
# You'll need to create these resources in the AWS Bedrock console
# and update these values with the actual IDs

# Agent ID for the P2P lending assistant
# Find this in the Bedrock console under Agents
BEDROCK_AGENT_ID = ""

# Agent Alias ID for the P2P lending assistant
# Find this in the Bedrock console under Agents > Your Agent > Aliases
BEDROCK_AGENT_ALIAS_ID = ""

# Knowledge Base ID for P2P lending information
# Find this in the Bedrock console under Knowledge bases
BEDROCK_KNOWLEDGE_BASE_ID = ""

# Foundation Model ID for direct invocations
# Common options:
# - anthropic.claude-3-sonnet-20240229-v1:0 (recommended)
# - anthropic.claude-3-haiku-20240307-v1:0 (faster)
# - amazon.titan-text-express-v1
BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

# S3 bucket for storing P2P lending documents
# Create this in the S3 console
S3_BUCKET = ""
S3_PREFIX = "p2p-lending/"

def get_bedrock_resources():
    """
    Returns a dictionary with all Bedrock resource IDs.
    """
    return {
        'agent_id': BEDROCK_AGENT_ID,
        'agent_alias_id': BEDROCK_AGENT_ALIAS_ID,
        'knowledge_base_id': BEDROCK_KNOWLEDGE_BASE_ID,
        'model_id': BEDROCK_MODEL_ID,
        's3_bucket': S3_BUCKET,
        's3_prefix': S3_PREFIX
    }
