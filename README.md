# P2P Lending Voice AI Assistant

A state-of-the-art voice AI assistant designed to educate potential users about Peer-to-Peer lending and guide them through the initial sales and onboarding process. This application uses advanced speech recognition and synthesis capabilities to create natural, human-like conversation flows.

## Key Features

- **Voice Input**: Natural speech recognition using OpenAI's Whisper model
- **Voice Output**: Human-like speech synthesis using OpenAI's TTS API
- **Contextual Memory**: Remembers conversation history for cohesive interactions
- **P2P Lending Knowledge**: Extensive knowledge base about P2P lending concepts
- **Empathetic Responses**: Human-like responses with discourse markers and natural transitions
- **Web Interface**: Modern, intuitive web UI for both voice and text interactions

## Project Structure

```
voicebot_submission/
├── main.py                 # Main entry point for the CLI demo
├── server.py               # Flask web server for the web interface
├── start_web.py            # Starter script for the web application
├── run_inference.py        # Script for Round 1 evaluation
├── requirements.txt        # Python dependencies
├── static/                 # Web frontend assets
│   ├── index.html          # Main web interface
│   ├── css/                # CSS styles
│   ├── js/                 # JavaScript files
│   └── audio/              # Generated audio files (created at runtime)
├── config/
│   └── config.yaml         # Configuration settings
├── modules/
│   ├── asr_module.py       # Automatic Speech Recognition module
│   ├── tts_module.py       # Text-to-Speech module
│   ├── nlp_pipeline.py     # NLP processing pipeline
│   ├── response_gen.py     # Response generation module
│   ├── fallback_service.py # Fallback service for handling errors
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

You can also run `python start_web.py` which will create a `.env` file from the template if it doesn't exist.

## Running the Application

### Web Interface (Recommended)

Run the web application:
```
python start_web.py
```

This will:
1. Start a Flask web server on http://localhost:5000
2. Open your default browser to the web interface
3. Allow you to interact with the assistant using either voice or text

Options:
- `--port PORT`: Specify a different port (default: 5000)
- `--no-browser`: Don't automatically open the browser
- `--debug`: Run in debug mode

### Command-Line Demo

Run the command-line application with voice interaction:
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

## Web Interface Instructions

1. Open the web interface in your browser (http://localhost:5000)
2. The assistant will greet you with a welcome message
3. You can toggle between Voice mode and Text mode using the buttons at the top
4. In Voice mode:
   - Click the microphone button to start recording
   - Speak clearly into your microphone
   - Click the microphone again to stop recording (or it will stop automatically after 10 seconds)
   - The assistant will process your speech and respond
5. In Text mode:
   - Type your message in the text input field
   - Press Enter or click the Send button
   - The assistant will process your text and respond

## Advanced Features

- **Low Latency**: Optimized for quick response times and speech processing
- **Conversation Context**: Maintains history to provide coherent responses
- **Graceful Error Handling**: Elegantly recovers from ambiguous requests
- **Proactive Guidance**: Suggests next topics to explore in P2P lending
- **Discourse Markers**: Uses natural pauses and transitions for human-like speech
- **Fallback System**: Provides meaningful responses even when the backend is unavailable

## API Requirements

The application expects the following environment variables:
- `API_GATEWAY_URL`: The base URL for the AWS API Gateway
- `API_GATEWAY_KEY`: The API key for authentication
- `OPENAI_API_KEY`: OpenAI API key for ASR and TTS services

## Notes for Evaluators

- The web interface provides a much more intuitive experience than the command-line version
- The frontend is responsive and works on both desktop and mobile devices
- The system is designed to gracefully handle errors and connectivity issues
- All conversation history is maintained within the session
- The application will try to use real API services if configured, but will fall back to demo mode if they are unavailable

## Contributors

Developed by Team Innovators for the AI-Humanized Voicebot Hackathon.