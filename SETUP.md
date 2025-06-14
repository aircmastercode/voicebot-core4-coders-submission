# P2P Lending Voice AI Assistant Setup Guide

This guide will help you set up and run the complete P2P Lending Voice AI Assistant, which consists of:
1. Python backend for NLP processing and API endpoints
2. React frontend for user interaction

## Prerequisites

- Python 3.7+ with pip
- Node.js 14+ with npm
- OpenAI API key (for ASR and TTS)
- AWS credentials (if using AWS services)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/p2p-lending-assistant.git
cd p2p-lending-assistant
```

### 2. Environment Setup

Create a `.env` file in the project root with the following variables:
```
# OpenAI API Key (required for ASR and TTS)
OPENAI_API_KEY=your-openai-api-key

# AWS Configuration (required for AWS Bedrock)
API_GATEWAY_URL=https://your-api-gateway-url.amazonaws.com/dev
API_GATEWAY_KEY=your-api-key
KNOWLEDGE_BASE_ID=your-knowledge-base-id
S3_BUCKET_NAME=your-s3-bucket
```

### 3. Python Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Flask API server:
```bash
python server.py
```

The backend server will start on http://localhost:5000

### 4. React Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install frontend dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at http://localhost:3000

## Using the Application

1. Open your browser to http://localhost:3000
2. You can interact with the assistant in two ways:
   - Type your questions in the text field
   - Click the microphone button to use voice input

## Troubleshooting

### API Connection Issues
- Make sure the Flask server is running
- Check if the `.env` file contains valid API keys
- Look for CORS errors in the browser console

### Voice Recognition Issues
- Ensure your microphone permissions are enabled in the browser
- Check if your OpenAI API key is valid
- Try using a different browser if issues persist

### Backend Errors
- Check the Flask server console for error logs
- Ensure all required environment variables are set
- Verify that your AWS services are properly configured

## Architecture Overview

### Backend Components
- `server.py`: Flask server that handles API requests
- `modules/asr_module.py`: Handles voice-to-text conversion
- `modules/tts_module.py`: Handles text-to-voice conversion
- `modules/nlp_pipeline.py`: Processes text and communicates with AWS services
- `modules/response_gen.py`: Generates final responses

### Frontend Components
- React application with Material UI
- Voice recording functionality
- Chat interface for conversation history
- Text-to-speech playback for responses 