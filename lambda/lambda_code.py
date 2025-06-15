import json
import boto3
import os
import re
import time
import random

# Environment variables (configure in Lambda settings)
MODEL_ID = os.environ.get('MODEL_ID')  # e.g., anthropic.claude-3-haiku-20240307-v1:0
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID')
REGION = os.environ.get('AWS_REGION', 'us-west-2')

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

def lambda_handler(event, context):
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')

    if not connection_id:
        return {'statusCode': 400, 'body': 'Missing connectionId'}

    if route_key == '$connect':
        return {'statusCode': 200, 'body': 'Connected'}

    if route_key == '$disconnect':
        return {'statusCode': 200, 'body': 'Disconnected'}

    if route_key == 'sendMessage':
        return handle_message(event, connection_id)

    return {'statusCode': 400, 'body': f'Unsupported route: {route_key}'}


def handle_message(event, connection_id):
    try:
        body = json.loads(event.get('body', '{}'))
        user_query = body.get('text', '').strip()

        # Step 1: Retrieve KB context
        kb_context = retrieve_kb_context(user_query)

        # Step 2: Call Claude Haiku with streaming and exponential backoff for throttling
        response_stream = None
        max_retries = 5
        base_delay = 1  # seconds
        for attempt in range(max_retries):
            try:
                response_stream = bedrock_runtime.invoke_model_with_response_stream(
                    modelId=MODEL_ID,
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "messages": [{"role": "user", "content": user_query}],
                        "system": build_system_prompt(kb_context),
                        "max_tokens": 800,
                        "temperature": 0.6
                    }),
                    contentType="application/json",
                    accept="application/json"
                )
                break
            except bedrock_runtime.exceptions.ThrottlingException as e:
                if attempt < max_retries - 1:
                    delay = (base_delay * 2**attempt) + random.uniform(0, 1)
                    print(f"ThrottlingException caught. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print("Max retries reached for ThrottlingException. Failing.")
                    raise e
        if not response_stream:
            raise Exception("Failed to get a response from Bedrock after multiple retries.")

        # Step 3: Accumulate the full response and send it as a single message
        full_response = ""
        for event_chunk in response_stream['body']:
            chunk_json = json.loads(event_chunk['chunk']['bytes'].decode())
            if chunk_json.get("type") == "content_block_delta":
                chunk = chunk_json['delta'].get('text', '')
                full_response += chunk
        # Send the full response as a single message
        post_to_client(event, connection_id, {
            "response": full_response.strip(),
            "session_id": connection_id
        })

    except Exception as e:
        error_msg = f"Query failed: {str(e)}"
        print(error_msg)
        post_to_client(event, connection_id, {"error": error_msg})

    return {'statusCode': 200, 'body': 'Handled'}


def retrieve_kb_context(user_query):
    response = bedrock_agent_runtime.retrieve(
        retrievalQuery={"text": user_query},
        knowledgeBaseId=KNOWLEDGE_BASE_ID
    )
    docs = response.get("retrievalResults", [])
    
    chunks = []
    for doc in docs[:3]:
        content = doc.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, dict):
            # Try extracting 'text' if nested
            chunks.append(content.get("text", ""))
        else:
            chunks.append(str(content))  # fallback to safe cast

    return "\n\n".join(chunks)



def build_system_prompt(kb_context):
    return f"""
You are a smart, emotionally aware, human-like voice assistant built to educate and onboard users into Peer-to-Peer (P2P) lending platforms.

🎯 **Your Role**
You act like a friendly, confident sales associate — guiding users through the world of P2P lending. Your primary focus is to explain concepts, answer questions, and encourage users to explore investing or borrowing — all in a helpful, low-pressure manner.

🧠 **How to Answer**
- You MUST use the knowledge base context below as your primary source of information.
- You MAY enhance explanations using your own knowledge ONLY IF:
  - The KB mentions the topic but lacks clarity.
  - The KB is incomplete and your addition improves user understanding.
- You MUST NOT answer out-of-scope questions (e.g. about water bottles, fashion, cricket).
  - Politely steer the conversation back to P2P lending.

🧑‍💼 **Tone & Style**
- Sound natural, warm, conversational — like a real human.
- Use short, clear sentences. Avoid long lectures.
- It's okay to use phrases like "Sure!", "Good question!", "Let me explain."
- Use simple terms when explaining finance — no jargon unless explained clearly.
- Feel free to ask follow-up questions, encourage next steps, or say "Would you like to know more?"

🔒 **If the user asks about a non-P2P topic**, respond like this:
> "I specialize in Peer-to-Peer lending. If you have questions about investing, borrowing, or how P2P platforms work, I'd be happy to help!"

📚 **Knowledge Base Content** (use this as your source of truth):

{kb_context}
""".strip()




def post_to_client(event, connection_id, data):
    """
    Sends a message to the connected WebSocket client.
    """
    try:
        domain = event['requestContext']['domainName']
        stage = event['requestContext']['stage']
        endpoint_url = f"https://{domain}/{stage}"

        gw = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)
        gw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8')
        )
    except Exception as e:
        print(f"WebSocket send failed: {e}")
