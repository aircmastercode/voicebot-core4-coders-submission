#!/usr/bin/env python3
"""
P2P Lending Awareness & Sales Voice AI Assistant - Inference Script

This script is crucial for Round 1 evaluation. It reads questions from an input file,
generates responses using the assistant's NLP and response generation components,
and writes the responses to an output file.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

# Import modules
try:
    from modules.nlp_pipeline import NLPPipeline
    from modules.response_gen import ResponseGenerator
    from modules.utils import setup_logger, load_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed all dependencies with 'pip install -r requirements.txt'")
    sys.exit(1)

# Setup logging
logger = logging.getLogger(__name__)


class InferenceEngine:
    """Inference engine for processing questions and generating responses."""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize the inference engine with configuration.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Setup logging
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', 'logs/inference.log')
        setup_logger(log_level, log_file)
        
        logger.info("Initializing Inference Engine")
        
        # Initialize components
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialize required components for inference."""
        try:
            # Initialize NLP Pipeline
            logger.info("Initializing NLP Pipeline")
            self.nlp = NLPPipeline(self.config)
            
            # Initialize Response Generator
            logger.info("Initializing Response Generator")
            self.response_gen = ResponseGenerator(self.config)
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def process_file(self, input_file, output_file):
        """Process questions from input file and write responses to output file.
        
        Args:
            input_file (str): Path to input file with questions
            output_file (str): Path to output file for responses
        """
        logger.info(f"Processing questions from {input_file}")
        
        try:
            # Read questions from input file
            with open(input_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Found {len(questions)} questions to process")
            
            # Process each question and generate responses
            responses = []
            context = {}  # Maintain context across questions
            
            for question in tqdm(questions, desc="Processing questions"):
                # Process through NLP pipeline
                nlp_result = self.nlp.process(question, context)
                
                # Generate response
                response = self.response_gen.generate_response(
                    question,
                    intent=nlp_result['intent'],
                    entities=nlp_result['entities'],
                    context=nlp_result['context']
                )
                
                # Update context for next question
                context = nlp_result['context']
                
                # Add response to list
                responses.append(response)
            
            # Write responses to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                for response in responses:
                    f.write(f"{response}\n")
            
            logger.info(f"Successfully wrote {len(responses)} responses to {output_file}")
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise


def main():
    """Main function to parse arguments and run inference."""
    parser = argparse.ArgumentParser(description="P2P Lending Voice AI Assistant - Inference")
    parser.add_argument(
        "--input", 
        required=True,
        help="Path to input file with questions"
    )
    parser.add_argument(
        "--output", 
        required=True,
        help="Path to output file for responses"
    )
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        # Create inference engine
        engine = InferenceEngine(config_path=args.config)
        
        # Process file
        engine.process_file(args.input, args.output)
        
        print(f"Successfully processed {args.input} and wrote responses to {args.output}")
        
    except Exception as e:
        logger.error(f"Error running inference: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()