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
import asyncio

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

# --- Start of new async processing logic ---

async def process_question_concurrently(question: str, nlp_pipeline: NLPPipeline, semaphore: asyncio.Semaphore):
    """
    Processes a single question asynchronously, respecting the semaphore limit.
    """
    async with semaphore:
        if not isinstance(question, str) or not question.strip():
            return "Invalid question provided."
        try:
            # Await the async process_input method directly
            nlp_data = await nlp_pipeline.process_input(question)
            final_response = response_generator.get_final_answer(nlp_data)
            return final_response
        except Exception as e:
            logging.error(f"An error occurred while processing question: '{question}'. Error: {e}")
            return "Error processing this question."

async def main(input_path: str, output_path: str, concurrency_limit: int = 20):
    """
    Main async function to run the inference process concurrently.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting concurrent inference process...")

    # 1. Initialize modules (same as before)
    try:
        logger.info("Loading configuration...")
        config = NLPConfig.from_yaml()
        
        logger.info("Initializing NLP Pipeline...")
        # Note: NLPPipeline will be shared across all tasks
        global nlp_pipeline
        nlp_pipeline = NLPPipeline(config=config)
        
        logger.info("Initializing Response Generator...")
        global response_generator
        response_generator = ResponseGenerator()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize modules: {e}")
        return

    # 2. Read input data (same as before)
    try:
        logger.info(f"Reading input questions from {input_path}")
        input_df = pd.read_csv(input_path)
        if "Questions" not in input_df.columns:
            logger.error("Input CSV must contain a 'Questions' column.")
            return
    except FileNotFoundError:
        logger.error(f"Input file not found at {input_path}")
        return

    # 3. Create and run concurrent tasks
    semaphore = asyncio.Semaphore(concurrency_limit)
    tasks = []
    logger.info(f"Creating {len(input_df)} tasks with a concurrency limit of {concurrency_limit}...")
    
    for question in input_df["Questions"]:
        tasks.append(process_question_concurrently(question, nlp_pipeline, semaphore))

    # tqdm can be used with asyncio for progress bars
    # Using asyncio.gather to wait for all tasks to complete
    responses = await asyncio.gather(*tasks)

    # 4. Save results (same as before)
    logger.info(f"Saving responses to {output_path}")
    output_df = input_df.copy()
    output_df["Responses"] = responses
    output_df.to_csv(output_path, index=False)

    logger.info("Concurrent inference process completed successfully.")
    
    # Gracefully close the pipeline resources
    await nlp_pipeline.close()

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
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of API requests to run in parallel."
    )

    args = parser.parse_args()
    # Run the main async function
    asyncio.run(main(args.input, args.output, args.concurrency))
# --- End of new async processing logic ---