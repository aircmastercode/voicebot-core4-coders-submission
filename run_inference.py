# #!/usr/bin/env python3
# """
# P2P Lending Awareness & Sales Voice AI Assistant - Inference Script

# This script is crucial for Round 1 evaluation. It reads questions from an input file,
# generates responses using the assistant's NLP and response generation components,
# and writes the responses to an output file.
# """

# import os
# import sys
# import argparse
# import logging
# from dotenv import load_dotenv
# from pathlib import Path
# from tqdm import tqdm
# import pandas as pd
# import asyncio

# # Add the project root to the Python path to allow for module imports
# sys.path.append('.')

# # Import modules
# try:
#     from modules.nlp_pipeline import NLPPipeline, NLPConfig
#     from modules.response_gen import ResponseGenerator
#     from modules.utils import setup_logger, load_config
# except ImportError as e:
#     print(f"Error importing modules: {e}")
#     print("Make sure you've installed all dependencies with 'pip install -r requirements.txt'")
#     sys.exit(1)

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # --- Start of new async processing logic ---

# async def process_question_concurrently(question: str, config: NLPConfig, semaphore: asyncio.Semaphore):
#     """
#     Processes a single question asynchronously, respecting the semaphore limit.
#     Each task gets its own NLPPipeline and WebSocket connection.
#     """
#     async with semaphore:
#         if not isinstance(question, str) or not question.strip():
#             return "Invalid question provided."
#         try:
#             nlp_pipeline = NLPPipeline(config=config)
#             response_generator = ResponseGenerator()
#             nlp_data = await nlp_pipeline.process_input(question)
#             final_response = response_generator.get_final_answer(nlp_data)
#             await nlp_pipeline.close()
#             return final_response
#         except Exception as e:
#             logging.error(f"An error occurred while processing question: '{question}'. Error: {e}")
#             return "Error processing this question."

# async def main(input_path: str, output_path: str, concurrency_limit: int = 1):
#     """
#     Main async function to run the inference process concurrently and update the CSV in real-time.
#     """
#     logger = logging.getLogger(__name__)
#     logger.info("Starting real-time inference process...")

#     # 1. Initialize config (shared, safe)
#     try:
#         logger.info("Loading configuration...")
#         config = NLPConfig.from_yaml()
#     except (FileNotFoundError, ValueError) as e:
#         logger.error(f"Failed to initialize config: {e}")
#         return

#     # 2. Read input data and prepare the output file for real-time updates
#     try:
#         logger.info(f"Reading input questions from {input_path}")
#         input_df = pd.read_csv(input_path)
#         if "Questions" not in input_df.columns:
#             logger.error("Input CSV must contain a 'Questions' column.")
#             return
#         input_df["Responses"] = "[Processing...]"
#         input_df.to_csv(output_path, index=False)
#     except FileNotFoundError:
#         logger.error(f"Input file not found at {input_path}")
#         return

#     # 3. Create, run, and process tasks in real-time
#     semaphore = asyncio.Semaphore(concurrency_limit)
#     future_to_index = {
#         asyncio.create_task(process_question_concurrently(row["Questions"], config, semaphore)): index
#         for index, row in input_df.iterrows()
#     }
#     logger.info(f"Processing {len(input_df)} questions in real-time with a concurrency of {concurrency_limit}...")
#     for future in tqdm(asyncio.as_completed(future_to_index), total=len(input_df), desc="Generating Responses"):
#         try:
#             response = await future
#             index = future_to_index[future]
#             input_df.loc[index, 'Responses'] = response
#             input_df.to_csv(output_path, index=False)
#         except Exception as e:
#             logger.error(f"A task failed: {e}")
#     logger.info("Real-time inference process completed successfully.")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Run inference to generate responses for a list of questions.")
#     parser.add_argument(
#         "--input",
#         type=str,
#         default="test.csv",
#         help="Path to the input CSV file containing a 'Questions' column."
#     )
#     parser.add_argument(
#         "--output",
#         type=str,
#         default="submission.csv",
#         help="Path to save the output CSV file with the generated 'Responses' column."
#     )
#     parser.add_argument(
#         "--concurrency",
#         type=int,
#         default=1,
#         help="Number of API requests to run in parallel. Default is 1 to avoid rate limiting."
#     )

#     args = parser.parse_args()
#     # Run the main async function
#     asyncio.run(main(args.input, args.output, args.concurrency))
# # --- End of new real-time processing logic ---
import os
import sys
import argparse
import logging
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import asyncio
import csv
# Add the project root to the Python path to allow for module imports
sys.path.append('.')

try:
    from modules.nlp_pipeline import NLPPipeline, NLPConfig
    from modules.response_gen import ResponseGenerator
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_question_concurrently(index, question, config, semaphore, queue):
    async with semaphore:
        try:
            nlp_pipeline = NLPPipeline(config=config)
            response_generator = ResponseGenerator()
            nlp_data = await nlp_pipeline.process_input(question)
            final_response = response_generator.get_final_answer(nlp_data)
            await nlp_pipeline.close()
            await queue.put((index, final_response))
        except Exception as e:
            logging.error(f"Error processing question at index {index}: {e}")
            await queue.put((index, "Error processing this question."))

async def writer_task(queue, input_df, output_path, total):
    processed = 0
    with tqdm(total=total, desc="Generating Responses") as pbar:
        while processed < total:
            index, response = await queue.get()
            input_df.loc[index, 'Responses'] = response
            input_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
            pbar.update(1)
            processed += 1

async def main(input_path, output_path, concurrency_limit=1):
    logger = logging.getLogger(__name__)
    logger.info("Starting real-time inference process...")

    try:
        logger.info("Loading configuration...")
        config = NLPConfig.from_yaml()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to initialize config: {e}")
        return

    try:
        logger.info(f"Reading input questions from {input_path}")
        input_df = pd.read_csv(input_path)
        if "Questions" not in input_df.columns:
            logger.error("Input CSV must contain a 'Questions' column.")
            return
        input_df["Responses"] = "[Processing...]"
        input_df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    except FileNotFoundError:
        logger.error(f"Input file not found at {input_path}")
        return

    semaphore = asyncio.Semaphore(concurrency_limit)
    queue = asyncio.Queue()
    tasks = [
        asyncio.create_task(process_question_concurrently(index, row["Questions"], config, semaphore, queue))
        for index, row in input_df.iterrows()
    ]
    writer = asyncio.create_task(writer_task(queue, input_df, output_path, len(tasks)))
    await asyncio.gather(*tasks)
    await writer

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
        default=1,
        help="Number of API requests to run in parallel. Default is 1 to avoid rate limiting."
    )

    args = parser.parse_args()
    asyncio.run(main(args.input, args.output, args.concurrency))