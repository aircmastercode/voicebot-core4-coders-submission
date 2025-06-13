# P2P Lending Awareness & Sales Voice AI Assistant

A voice-enabled AI assistant designed to educate users about P2P lending, guide them through the onboarding process, and answer queries with human-like conversational abilities.

## Features

- **Hyper-realistic voice synthesis** with emotional resonance
- **Near-zero latency** interaction
- **Multilingual support** (English, Hindi, Hinglish)
- **Advanced acoustic clarity** with noise cancellation
- **Conversational nuance** with discourse markers
- **Deep contextual memory** for long conversations
- **Proactive conversational guidance**
- **Elegant error handling**

## Project Structure

```
.
├── config/                 # Configuration files
│   └── config.yaml        # Main configuration
├── data/                  # Data directory
│   └── knowledge/         # P2P lending knowledge base
├── modules/               # Core modules
│   ├── asr_module.py     # Automatic Speech Recognition
│   ├── nlp_pipeline.py   # NLP processing pipeline
│   ├── response_gen.py   # Response generation
│   └── utils.py          # Utility functions
├── tests/                 # Test directory
├── .env.example           # Example environment variables
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
└── run_inference.py       # Script for inference on test data
```

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository (if not already done)
# git clone <repository-url>

# Navigate to the project directory
cd /path/to/Project2.0Matrix

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Keys and Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your API keys:
   - **OpenAI API Key**: For Whisper ASR and GPT-4
   - **ElevenLabs API Key**: For voice synthesis
   - Other optional API keys as needed

### 3. Knowledge Base Setup

The system uses P2P lending documents for its knowledge base. These are automatically loaded from the `data/knowledge` directory.

## Running the Application

### Main Application

To start the voice assistant in interactive mode:

```bash
python main.py
```

### Inference Mode

For Round 1 evaluation, run the inference script which processes test questions and generates responses:

```bash
python run_inference.py --input path/to/questions.txt --output path/to/responses.txt
```

## Configuration

The application is configured through `config/config.yaml`. Key configuration sections include:

- **API Configuration**: Settings for ASR, TTS, and LLM services
- **Audio Processing**: Input/output settings and noise cancellation
- **NLP Pipeline**: Intent recognition, entity extraction, and context management
- **Voice Synthesis**: Voice profiles and emotion mapping
- **Knowledge Base**: Vector database settings
- **Performance**: Caching and optimization settings

## Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for Whisper ASR and GPT-4 | Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for voice synthesis | Yes |
| `ASR_SERVICE_PROVIDER` | ASR service provider (default: whisper) | No |
| `TTS_SERVICE_PROVIDER` | TTS service provider (default: elevenlabs) | No |
| `LLM_SERVICE_PROVIDER` | LLM service provider (default: openai) | No |
| `DEBUG_MODE` | Enable debug mode (default: false) | No |

## Testing

Run the test suite with:

```bash
python -m pytest
```

## License

[Specify License]