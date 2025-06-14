#!/usr/bin/env python3
"""
<<<<<<< HEAD
P2P Lending API Backend Server

This server acts as a bridge between the React frontend and the NLP backend.
It handles API requests and forwards them to the appropriate services.
=======
P2P Lending Voice AI Assistant - Web Server

This script provides a Flask web server that:
1. Serves the frontend web interface
2. Provides API endpoints for text and speech processing
3. Integrates with the existing NLP pipeline, ASR, and TTS modules
>>>>>>> b1e7711 (made frontend and now the audio will get stored to s3)
"""

import os
import sys
import json
<<<<<<< HEAD
import base64
import tempfile
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
=======
import logging
import tempfile
import uuid
import random
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, send_file
>>>>>>> b1e7711 (made frontend and now the audio will get stored to s3)

# Add the project root to the Python path
sys.path.append('.')

<<<<<<< HEAD
# Import modules
from modules.asr_module import ASRModule, ASRConfig
from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

=======
>>>>>>> b1e7711 (made frontend and now the audio will get stored to s3)
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

<<<<<<< HEAD
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
=======
# Global initialization status
MODULES_INITIALIZED = False

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Import modules
try:
    from modules.asr_module import ASRModule, ASRConfig
    from modules.tts_module import TTSModule, TTSConfig
    from modules.nlp_pipeline import NLPPipeline, NLPConfig
    from modules.response_gen import ResponseGenerator
    from modules.fallback_service import FallbackService

    logger.info("Loading configurations...")
    asr_config = ASRConfig.from_yaml()
    tts_config = TTSConfig.from_yaml()
    nlp_config = NLPConfig.from_yaml()
    
    logger.info("Initializing modules...")
    asr_module = ASRModule(config=asr_config)
    tts_module = TTSModule(config=tts_config)
    nlp_pipeline = NLPPipeline(config=nlp_config)
    response_generator = ResponseGenerator()
    fallback_service = FallbackService()
    
    logger.info("All modules initialized successfully")
    MODULES_INITIALIZED = True
    
except Exception as e:
    logger.error(f"Error initializing modules: {e}")
    logger.warning("Loading fallback service...")
    try:
        from modules.fallback_service import FallbackService
        fallback_service = FallbackService()
        logger.info("Fallback service loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load fallback service: {e}")
    logger.error("Server will have limited functionality")

# Create audio storage directory
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Demo mode canned responses
DEMO_RESPONSES = {
    "definition": "P2P lending (peer-to-peer lending) connects individual lenders directly with borrowers through online platforms, bypassing traditional banks. Lenders can earn interest on their investments while borrowers may get more favorable rates than from conventional sources.",
    
    "risks": "P2P lending involves several risks, including credit default risk (borrowers failing to repay), platform risk (the platform itself could fail), liquidity risk (difficulty withdrawing funds before loan maturity), and regulatory risk (changing regulations could impact returns).",
    
    "benefits": "P2P lending offers potentially higher returns for investors compared to traditional savings accounts, more favorable rates for borrowers, portfolio diversification, and accessibility for those who might not qualify for traditional bank loans.",
    
    "regulation": "In India, P2P lending platforms are regulated by the Reserve Bank of India (RBI) and must be registered as Non-Banking Financial Companies (NBFC-P2P). This regulation helps protect both lenders and borrowers by ensuring platforms operate transparently.",
    
    "default": "That's a great question about P2P lending! In a peer-to-peer lending model, investors can earn returns by lending directly to borrowers through an online platform that matches lenders with borrowers. The platform handles the loan origination, credit checks, and payment processing, while providing transparency and portfolio diversification options for lenders."
}

# Routes
@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    status = "ok" if MODULES_INITIALIZED else "limited"
    return jsonify({"status": status, "modules_initialized": MODULES_INITIALIZED}), 200

@app.route('/api/text', methods=['POST'])
def process_text():
    """Process text input from the user"""
    try:
        data = request.json
        user_text = data.get('text')
        history = data.get('history', [])
        
        if not user_text:
            return jsonify({"error": "No text provided"}), 400
        
        # Create a unique session ID for this conversation
        session_id = str(uuid.uuid4())
        
        logger.info(f"Processing text input: '{user_text}'")
        
        final_response = ""
        
        if MODULES_INITIALIZED:
            try:
                # Process the text through the NLP pipeline
                nlp_data = nlp_pipeline.process_input(
                    user_text, 
                    session_id=session_id,
                    history=history
                )
                
                # Check if we should use fallback
                if fallback_service.should_use_fallback(nlp_data):
                    logger.warning("NLP pipeline returned invalid data, using fallback")
                    final_response = fallback_service.get_fallback_response(user_text, history)
                else:
                    # Generate the final response
                    final_response = response_generator.get_final_answer(nlp_data)
            except Exception as e:
                logger.error(f"Error in NLP processing: {e}", exc_info=True)
                final_response = fallback_service.get_fallback_response(user_text, history)
        else:
            # Use fallback service if modules are not initialized
            try:
                final_response = fallback_service.get_fallback_response(user_text, history)
            except Exception:
                final_response = "I'm sorry, I'm experiencing technical difficulties right now. Please try again later."
        
        # Generate speech for the response
        audio_file = None
        audio_url = None
        
        try:
            if MODULES_INITIALIZED:
                # Generate a unique filename
                audio_filename = f"{uuid.uuid4()}.mp3"
                audio_path = AUDIO_DIR / audio_filename
                
                # Convert response to speech
                audio_file = tts_module.text_to_speech(final_response, str(audio_path))
                audio_url = f"/static/audio/{audio_filename}" if audio_file else None
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
        
        # Return the response
        return jsonify({
            "response": final_response,
            "audio_url": audio_url
        })
        
    except Exception as e:
        logger.error(f"Error processing text request: {e}", exc_info=True)
        error_response = "I'm sorry, I'm experiencing technical difficulties. Please try again later."
        return jsonify({"error": "Failed to process your request", "response": error_response}), 500

@app.route('/api/speech', methods=['POST'])
def process_speech():
    """Process speech input from the user"""
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        history_json = request.form.get('history', '[]')
        
        try:
            history = json.loads(history_json)
        except json.JSONDecodeError:
            history = []
            
        # Create a unique session ID for this conversation
        session_id = str(uuid.uuid4())
        
        # Save the audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        transcription = ""
        final_response = ""
        audio_url = None
        
        # Transcribe the audio
        try:
            if MODULES_INITIALIZED:
                transcription = asr_module.transcribe_file(temp_path)
            else:
                # Fallback for demonstration
                transcription = "This is a demo transcription as the ASR module is not available."
                
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            if not transcription:
                return jsonify({"error": "Could not transcribe audio"}), 400
                
            logger.info(f"Transcribed speech: '{transcription}'")
            
            if MODULES_INITIALIZED:
                try:
                    # Process the transcription through the NLP pipeline
                    nlp_data = nlp_pipeline.process_input(
                        transcription, 
                        session_id=session_id,
                        history=history
                    )
                    
                    # Check if we should use fallback
                    if fallback_service.should_use_fallback(nlp_data):
                        logger.warning("NLP pipeline returned invalid data, using fallback")
                        final_response = fallback_service.get_fallback_response(transcription, history)
                    else:
                        # Generate the final response
                        final_response = response_generator.get_final_answer(nlp_data)
                except Exception as e:
                    logger.error(f"Error in NLP processing: {e}", exc_info=True)
                    final_response = fallback_service.get_fallback_response(transcription, history)
            else:
                # Use fallback service if modules are not initialized
                try:
                    final_response = fallback_service.get_fallback_response(transcription, history)
                except Exception:
                    final_response = "I'm sorry, I'm experiencing technical difficulties right now. Please try again later."
            
            # Generate speech for the response
            try:
                if MODULES_INITIALIZED:
                    # Generate a unique filename
                    audio_filename = f"{uuid.uuid4()}.mp3"
                    audio_path = AUDIO_DIR / audio_filename
                    
                    # Convert response to speech
                    audio_file = tts_module.text_to_speech(final_response, str(audio_path))
                    audio_url = f"/static/audio/{audio_filename}" if audio_file else None
            except Exception as e:
                logger.error(f"Error generating speech response: {e}")
            
            # Return the response
            return jsonify({
                "text": transcription,
                "response": final_response,
                "audio_url": audio_url
            })
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
    except Exception as e:
        logger.error(f"Error processing speech request: {e}", exc_info=True)
        error_response = "I'm sorry, I'm experiencing technical difficulties. Please try again later."
        return jsonify({"error": "Failed to process your request", "response": error_response}), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    return send_from_directory(AUDIO_DIR, filename)

# Enhanced demo endpoints for frontend testing
@app.route('/api/demo/<mode>', methods=['POST'])
def demo_endpoint(mode):
    """Demo endpoint for frontend testing without backend dependencies"""
    logger.warning("Using demo endpoint - this should not be used in production")
    
    # Keywords to detect the topic for demo responses
    keywords = {
        "definition": ["what is", "define", "meaning", "explain", "understand", "basics", "concept"],
        "risks": ["risk", "danger", "safe", "safety", "concern", "problem", "default", "secure"],
        "benefits": ["benefit", "advantage", "return", "profit", "earn", "gain", "pros"],
        "regulation": ["regulation", "regulated", "legal", "law", "rbi", "compliant", "rules"]
    }
    
    if mode == 'text':
        data = request.json
        user_text = data.get('text', '').lower()
        
        # Detect the topic
        detected_topic = "default"
        for topic, topic_keywords in keywords.items():
            if any(keyword in user_text for keyword in topic_keywords):
                detected_topic = topic
                break
        
        # Get the appropriate response
        response = DEMO_RESPONSES.get(detected_topic, DEMO_RESPONSES["default"])
        
        return jsonify({
            "response": response
        })
        
    elif mode == 'speech':
        # For speech mode, we'll use what the user actually said if available
        # Extract audio data from request if available
        audio_data = request.files.get('audio')
        
        # If we have audio data, try to use it
        if audio_data:
            # Return a message that acknowledges the user's attempt to use voice
            return jsonify({
                "text": "I heard your voice input",
                "response": "I'm sorry, but voice recognition is currently unavailable due to missing API keys. Please try using the text input mode instead."
            })
        else:
            # Fallback to a generic message
            return jsonify({
                "text": "Voice input detected",
                "response": "I'm sorry, but voice recognition is currently unavailable due to missing API keys. Please try using the text input mode instead."
            })
        
    else:
        return jsonify({"error": "Invalid mode"}), 400

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the P2P Lending Voice AI Assistant web server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Start the server
    logger.info(f"Starting server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug) 
>>>>>>> b1e7711 (made frontend and now the audio will get stored to s3)
