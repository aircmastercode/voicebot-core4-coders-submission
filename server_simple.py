#!/usr/bin/env python3
"""
Simplified Backend Server for P2P Lending Voice AI Assistant

This version uses mock responses for testing the frontend connectivity
without any AWS or OpenAI dependencies.
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for all /api routes

# Sample responses for P2P lending questions
SAMPLE_RESPONSES = {
    "default": "I'm your P2P Lending Assistant. How can I help you today?",
    "what is p2p lending": "P2P lending (peer-to-peer lending) is a form of direct lending between individuals through online platforms, bypassing traditional financial institutions. It allows borrowers to get loans directly from investors, often with more favorable rates than traditional banks.",
    "risks": "The main risks of P2P lending include borrower default risk, platform risk (if the P2P company fails), liquidity risk (difficulty selling loans before maturity), interest rate risk, and regulatory uncertainty. Diversification across multiple loans is recommended to mitigate these risks.",
    "benefits": "P2P lending offers higher potential returns for investors compared to savings accounts, lower interest rates for borrowers than credit cards or payday loans, accessibility for those underserved by traditional banks, fast and easy online application processes, and portfolio diversification options.",
    "how": "To participate in P2P lending: 1) Research and choose a P2P platform, 2) Complete registration and verification, 3) As an investor, fund your account and select loans to invest in, or as a borrower, submit a loan application with required documentation, 4) Manage your investments or make regular loan repayments.",
    "regulations": "P2P lending regulations vary by country. Generally, platforms must register with financial authorities, follow anti-money laundering rules, maintain transparency in operations, and comply with consumer credit regulations. In the US, they're overseen by the SEC and state regulators; in the UK, by the FCA; and in India, by the RBI."
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Backend API is running'})

@app.route('/api/nlp', methods=['POST'])
def process_nlp():
    """Process NLP requests with mock responses."""
    try:
        data = request.json
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
            
        user_text = data['text'].lower()
        session_id = data.get('session_id', 'default-session')
        
        logger.info(f"Processing request: '{user_text[:50]}...' [session: {session_id}]")
        
        # Find the most relevant response
        response_text = SAMPLE_RESPONSES["default"]
        for key, response in SAMPLE_RESPONSES.items():
            if key in user_text:
                response_text = response
                break
        
        # Add a mock proactive suggestion
        response_text += "\n\nWould you like to know more about the risks or benefits of P2P lending?"
        
        return jsonify({
            'response': response_text,
            'session_id': session_id
        })
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Mock transcription endpoint."""
    try:
        data = request.json
        
        if not data or 'audio_data' not in data:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Just return a mock transcription
        sample_questions = [
            "What is P2P lending?",
            "What are the risks involved in P2P lending?",
            "What are the benefits of P2P lending?",
            "How do I start with P2P lending?",
            "Are there regulations for P2P lending?"
        ]
        
        import random
        transcription = random.choice(sample_questions)
        
        logger.info(f"Mock transcription: '{transcription}'")
        
        return jsonify({
            'transcription': transcription,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting simplified API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True) 