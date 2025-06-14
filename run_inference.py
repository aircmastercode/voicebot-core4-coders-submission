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
import pandas as pd

# Add the project root to the Python path to allow for module imports
sys.path.append('.')

# Import modules
try:
    from modules.nlp_pipeline import NLPPipeline, NLPConfig
    from modules.response_gen import ResponseGenerator
    from modules.utils import setup_logger, load_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed all dependencies with 'pip install -r requirements.txt'")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_inference(input_path: str, output_path: str):
    """
    Runs the inference process on a CSV file of questions.

    Args:
        input_path: Path to the input CSV file (e.g., 'test.csv').
        output_path: Path to save the output CSV file with responses.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting inference process...")

    # 1. Initialize modules
    try:
        logger.info("Loading configuration...")
        config = NLPConfig.from_yaml()
        
        logger.info("Initializing NLP Pipeline...")
        nlp_pipeline = NLPPipeline(config=config)
        
        logger.info("Initializing Response Generator...")
        response_generator = ResponseGenerator(config=config)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize modules: {e}")
        return

    # 2. Read input data
    try:
        logger.info(f"Reading input questions from {input_path}")
        input_df = pd.read_csv(input_path)
        if "Questions" not in input_df.columns:
            logger.error("Input CSV must contain a 'Questions' column.")
            return
    except FileNotFoundError:
        logger.error(f"Input file not found at {input_path}")
        return

    # 3. Process each question and generate responses
    responses = []
    logger.info(f"Processing {len(input_df)} questions...")
    for question in tqdm(input_df["Questions"], desc="Generating Responses"):
        if not isinstance(question, str) or not question.strip():
            responses.append("Invalid question provided.")
            continue

        try:
            # Step 1: Get structured data from the NLP pipeline
            nlp_data = nlp_pipeline.process_input(question)
            
            # Step 2: Generate the final response
            final_response = response_generator.generate_response(question, nlp_data)
            responses.append(final_response)
        except Exception as e:
            logger.error(f"An error occurred while processing question: '{question}'. Error: {e}")
            responses.append("Error processing this question.")

    # 4. Save results
    logger.info(f"Saving responses to {output_path}")
    output_df = input_df.copy()
    output_df["Responses"] = responses
    output_df.to_csv(output_path, index=False)

    logger.info("Inference process completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run inference to generate responses for a list of questions.")
    parser.add_argument(
        "--input",
        type=str,
        default="test.csv",
        help="Path to the input CSV file containing a 'Questions' column."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="submission.csv",
        help="Path to save the output CSV file with the generated 'Responses' column."
    )

    args = parser.parse_args()
    run_inference(args.input, args.output)