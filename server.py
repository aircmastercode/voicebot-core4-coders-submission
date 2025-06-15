#!/usr/bin/env python3
"""
P2P Lending Voice AI Assistant - Web Server

This script provides a Flask web server that:
1. Serves the frontend web interface
2. Provides API endpoints for text and speech processing
3. Integrates with the existing NLP pipeline, ASR, and TTS modules
"""

import os
import sys
import json
import logging
import tempfile
import uuid
import random
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, send_file
import threading

# Add the project root to the Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

@app.route('/elevenlabs')
def elevenlabs_demo():
    """Serve the ElevenLabs demo page"""
    return send_from_directory(app.static_folder, 'elevenlabs_demo.html')

@app.route('/speech-to-speech')
def speech_to_speech_demo():
    """Serve the Speech-to-Speech demo page"""
    return send_from_directory(app.static_folder, 'speech_to_speech.html')

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
                nlp_data = asyncio.run(nlp_pipeline.process_input(
                    user_text, 
                    session_id=session_id,
                    history=history
                ))
                
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
        
        # Generate a unique ID for the audio file that will be generated
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_url = f"/static/audio/{audio_filename}"
        
        # Start audio generation in a background thread
        def generate_audio_in_background():
            try:
                if MODULES_INITIALIZED:
                    # Generate a unique filename
                    audio_path = AUDIO_DIR / audio_filename
                    
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    
                    # Convert response to speech
                    audio_file = asyncio.run(tts_module.text_to_speech_file(final_response, str(audio_path)))
                    logger.info(f"Audio generation complete: {audio_url}")
            except Exception as e:
                logger.error(f"Error generating speech response: {e}")
        
        # Start the background thread for audio generation
        threading.Thread(target=generate_audio_in_background).start()
        
        # Return the response immediately with the expected audio URL
        return jsonify({
            "response": final_response,
            "audio_url": audio_url,
            "audio_status": "generating"  # Indicate that audio is being generated
        })
        
    except Exception as e:
        logger.error(f"Error processing text request: {e}", exc_info=True)
        error_response = "I'm sorry, I'm experiencing technical difficulties. Please try again later."
        return jsonify({"error": "Failed to process your request", "response": error_response}), 500

@app.route('/api/text_stream', methods=['POST'])
def process_text_stream():
    """Process text input from the user with streaming response"""
    try:
        data = request.json
        user_text = data.get('text')
        history = data.get('history', [])
        session_id = data.get('session_id')
        
        if not user_text:
            return jsonify({"error": "No text provided"}), 400
        
        # Create a unique session ID for this conversation if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Processing streaming text input: '{user_text}' with session ID: {session_id}")
        
        if MODULES_INITIALIZED:
            try:
                # Define stream handler
                def stream_handler(chunk):
                    logger.debug(f"Received chunk: {chunk}")
                
                # Process the text through the NLP pipeline with streaming
                # This is an async function, we need to run it with asyncio.run
                result = asyncio.run(nlp_pipeline.process_input(
                    user_text, 
                    session_id=session_id,
                    history=history,
                    stream_handler=stream_handler
                ))
                
                if result and "session_id" in result:
                    return jsonify({"status": "streaming", "session_id": result["session_id"]}), 200
                else:
                    return jsonify({"error": "Failed to start streaming"}), 500
            except Exception as e:
                logger.error(f"Error in streaming NLP processing: {e}", exc_info=True)
                return jsonify({"error": "Error processing streaming request"}), 500
        else:
            # Use fallback service if modules are not initialized
            return jsonify({
                "error": "Streaming not available in limited mode",
                "response": "I'm sorry, streaming responses are not available right now."
            }), 503
        
    except Exception as e:
        logger.error(f"Error processing streaming text request: {e}", exc_info=True)
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
                    # This is an async function, we need to await it
                    nlp_data = asyncio.run(nlp_pipeline.process_input(
                        transcription, 
                        session_id=session_id,
                        history=history
                    ))
                    
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
            
            # Generate a unique ID for the audio file that will be generated
            audio_filename = f"{uuid.uuid4()}.wav"
            audio_url = f"/static/audio/{audio_filename}"
            
            # Start audio generation in a background thread
            def generate_audio_in_background():
                try:
                    if MODULES_INITIALIZED:
                        # Generate a unique filename
                        audio_path = AUDIO_DIR / audio_filename
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                        
                        # Convert response to speech
                        audio_file = asyncio.run(tts_module.text_to_speech_file(final_response, str(audio_path)))
                        logger.info(f"Audio generation complete: {audio_url}")
                except Exception as e:
                    logger.error(f"Error generating speech response: {e}")
            
            # Start the background thread for audio generation
            threading.Thread(target=generate_audio_in_background).start()
            
            # Return the response immediately with the expected audio URL
            return jsonify({
                "text": transcription,
                "response": final_response,
                "audio_url": audio_url,
                "audio_status": "generating"  # Indicate that audio is being generated
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

@app.route('/api/speech-to-speech', methods=['POST'])
async def process_speech_to_speech():
    """Process speech input and return speech output"""
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        voice_id = request.form.get('voice_id', None)
        
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
            
            # Generate a unique ID for the audio file that will be generated
            audio_filename = f"{uuid.uuid4()}.wav"
            audio_url = f"/static/audio/{audio_filename}"
            
            # Process the transcription through the NLP pipeline
            if MODULES_INITIALIZED:
                try:
                    # Create a unique session ID for this conversation
                    session_id = str(uuid.uuid4())
                    
                    # Process the transcription through the NLP pipeline
                    nlp_data = await nlp_pipeline.process_input(
                        transcription, 
                        session_id=session_id,
                        history=[]
                    )
                    
                    # Check if we should use fallback
                    if fallback_service.should_use_fallback(nlp_data):
                        logger.warning("NLP pipeline returned invalid data, using fallback")
                        final_response = fallback_service.get_fallback_response(transcription, [])
                    else:
                        # Generate the final response
                        final_response = response_generator.get_final_answer(nlp_data)
                except Exception as e:
                    logger.error(f"Error in NLP processing: {e}", exc_info=True)
                    final_response = fallback_service.get_fallback_response(transcription, [])
            else:
                # Use fallback service if modules are not initialized
                try:
                    final_response = fallback_service.get_fallback_response(transcription, [])
                except Exception:
                    final_response = "I'm sorry, I'm experiencing technical difficulties right now. Please try again later."
            
            # Start audio generation in a background thread
            def generate_audio_in_background():
                try:
                    if MODULES_INITIALIZED:
                        # Generate a unique filename
                        audio_path = AUDIO_DIR / audio_filename
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                        
                        # Convert response to speech with the selected voice
                        tts_options = {}
                        if voice_id:
                            tts_options['voice_id'] = voice_id
                            
                        audio_file = asyncio.run(tts_module.text_to_speech_file(
                            final_response, 
                            str(audio_path), 
                            **tts_options
                        ))
                        logger.info(f"Audio generation complete: {audio_url}")
                except Exception as e:
                    logger.error(f"Error generating speech response: {e}")
            
            # Start the background thread for audio generation
            threading.Thread(target=generate_audio_in_background).start()
            
            # Return the response immediately with the expected audio URL
            return jsonify({
                "text": transcription,
                "response": final_response,
                "audio_url": audio_url,
                "audio_status": "generating"  # Indicate that audio is being generated
            })
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
    except Exception as e:
        logger.error(f"Error processing speech-to-speech request: {e}", exc_info=True)
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
        
        # Create a dummy audio URL to indicate TTS is not available
        # This will be handled by the frontend to show a message
        return jsonify({
            "response": response,
            "audio_url": None,
            "tts_status": "unavailable"
        })
        
    elif mode == 'speech':
        # For speech mode, we'll try to extract text from the form data if available
        history_json = request.form.get('history', '[]')
        
        try:
            history = json.loads(history_json)
        except json.JSONDecodeError:
            history = []
            
        # Extract the last user message from history if available
        user_query = ""
        if history:
            for msg in reversed(history):
                if msg.get('role') == 'user':
                    user_query = msg.get('content', '')
                    break
        
        # If we have audio data, acknowledge it
        if 'audio' in request.files:
            # Return a clear message about voice recognition being unavailable
            return jsonify({
                "text": user_query or "Voice input received",
                "response": "I'm sorry, but voice recognition is currently unavailable due to missing API keys. Please try using the text input mode instead.",
                "tts_status": "unavailable"
            })
        else:
            # Fallback to a generic message
            return jsonify({
                "text": "Voice input detected",
                "response": "I'm sorry, but voice recognition is currently unavailable due to missing API keys. Please try using the text input mode instead.",
                "tts_status": "unavailable"
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
