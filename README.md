# P2P Lending Voice AI Assistant

A state-of-the-art voice AI assistant designed to educate potential users about Peer-to-Peer lending and guide them through the initial sales and onboarding process. This application uses advanced speech recognition and synthesis capabilities to create natural, human-like conversation flows.

## Key Features

- **Voice Input**: Natural speech recognition using OpenAI's Whisper model
- **Voice Output**: Human-like speech synthesis using OpenAI's TTS API
- **Contextual Memory**: Remembers conversation history for cohesive interactions
- **P2P Lending Knowledge**: Extensive knowledge base about P2P lending concepts
- **Empathetic Responses**: Human-like responses with discourse markers and natural transitions

## Project Structure

```
voicebot_submission/
├── main.py                 # Main entry point for the live demo
├── run_inference.py        # Script for Round 1 evaluation
├── requirements.txt        # Python dependencies
├── config/
│   └── config.yaml         # Configuration settings
├── modules/
│   ├── asr_module.py       # Automatic Speech Recognition module
│   ├── tts_module.py       # Text-to-Speech module
│   ├── nlp_pipeline.py     # NLP processing pipeline
│   ├── response_gen.py     # Response generation module
│   ├── api_client.py       # API client for AWS services
│   └── utils.py            # Utility functions
├── data/
│   └── sample_audio.wav    # Sample audio for testing
└── output/                 # Directory for generated output
```

## Setup Instructions

### 1. Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/voicebot_submission.git
   cd voicebot_submission
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### 2. API Keys Configuration

Create a `.env` file in the project root with the following variables:
```
# AWS Configuration
API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com/dev
API_GATEWAY_KEY=your-api-gateway-key

# OpenAI API Key (for ASR and TTS)
OPENAI_API_KEY=your-openai-api-key
```

### 3. Knowledge Base Setup

The system uses an AWS Bedrock Knowledge Base through the Lambda function. The Lambda function should be configured with:
- Knowledge base ID
- AWS region
- S3 bucket for storing conversation history

## Running the Application

### Live Demo

Run the main application with voice interaction:
```
python main.py --mode voice
```

Or use text-only mode:
```
python main.py --mode text
```

### Round 1 Evaluation

Run the inference script on test data:
```
python run_inference.py --input test.csv --output submission.csv
```

## Voice Interaction Instructions

1. Start the application in voice mode
2. The assistant will greet you and wait for your input
3. Speak clearly when prompted
4. You can say "exit" to end the session or "text" to switch to text mode
5. In text mode, you can type "voice" to switch back to voice mode

## Advanced Features

- **Low Latency**: Optimized for quick response times and speech processing
- **Conversation Context**: Maintains history to provide coherent responses
- **Graceful Error Handling**: Elegantly recovers from ambiguous requests
- **Proactive Guidance**: Suggests next topics to explore in P2P lending
- **Discourse Markers**: Uses natural pauses and transitions for human-like speech

## API Requirements

The application expects the following environment variables:
- `API_GATEWAY_URL`: The base URL for the AWS API Gateway
- `API_GATEWAY_KEY`: The API key for authentication
- `OPENAI_API_KEY`: OpenAI API key for ASR and TTS services

## Notes for Evaluators

- The voice interaction can be tested with your system's microphone
- The ASR module is configured to listen for 5 seconds by default
- Response quality relies on both the LLM and the provided knowledge base
- All conversation history is maintained within the session

## Contributors

Developed by Team Innovators for the AI-Humanized Voicebot Hackathon.
hello commit_4