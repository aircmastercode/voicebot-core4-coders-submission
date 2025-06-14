#!/usr/bin/env python3
"""
P2P Lending API Backend Server

This server acts as a bridge between the React frontend and the NLP backend.
It handles API requests and forwards them to the appropriate services.
"""

import os
import sys
import json
import base64
import tempfile
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append('.')

# Import modules
from modules.asr_module import ASRModule, ASRConfig
from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize modules
try:
    logger.info("Loading configurations...")
    nlp_config = NLPConfig.from_yaml()
    asr_config = ASRConfig.from_yaml()
    
    logger.info("Initializing NLP Pipeline...")
    nlp_pipeline = NLPPipeline(config=nlp_config)
    
    logger.info("Initializing Response Generator...")
    response_generator = ResponseGenerator()
    
    logger.info("Initializing ASR Module...")
    asr_module = ASRModule(config=asr_config)
except (FileNotFoundError, ValueError) as e:
    logger.error(f"Failed to initialize modules: {e}")
    sys.exit(1)

@app.route('/api/nlp', methods=['POST'])
def process_nlp():
    """Process NLP requests and return responses."""
    try:
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        text = data['text']
        session_id = data.get('session_id', 'default-session')
        history = data.get('history', [])
        
        logger.info(f"Processing NLP request: {text[:50]}...")
        
        # Process the text through NLP pipeline
        nlp_data = nlp_pipeline.process_input(
            text=text,
            session_id=session_id,
            history=history
        )
        
        # Generate response
        final_response = response_generator.get_final_answer(nlp_data)
        
        return jsonify({
            'response': final_response,
            'session_id': session_id
        })
    except Exception as e:
        logger.error(f"Error processing NLP request: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using Whisper ASR."""
    try:
        data = request.json
        
        if not data or 'audio_data' not in data:
            return jsonify({'error': 'No audio data provided'}), 400
            
        # Get the base64 audio data
        audio_base64 = data['audio_data']
        audio_format = data.get('format', 'wav')
        
        # Decode base64 to binary
        audio_binary = base64.b64decode(audio_base64)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_format}') as temp_file:
            temp_file.write(audio_binary)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe
            logger.info("Transcribing audio...")
            transcription = asr_module.transcribe_file(temp_file_path)
            
            return jsonify({
                'transcription': transcription,
                'status': 'success'
            })
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Backend API is running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True) 