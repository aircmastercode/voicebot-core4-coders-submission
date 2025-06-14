#!/usr/bin/env python3
"""
Starter script for the P2P Lending Voice AI Assistant Web Application.
"""

import os
import sys
import subprocess
import webbrowser
import time
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check if the environment is properly set up."""
    logger.info("Checking environment setup...")
    
    # Check if .env file exists
    env_file_path = Path(".env")
    env_example_path = Path("config/env.sample")
    
    if not env_file_path.exists():
        logger.warning(".env file not found. Creating from sample file.")
        # Try to create from sample
        if env_example_path.exists():
            try:
                with open(env_example_path, 'r') as sample:
                    with open(env_file_path, 'w') as env_file:
                        env_file.write(sample.read())
                logger.info("Created .env file from sample. Please edit it with your API keys.")
            except Exception as e:
                logger.error(f"Failed to create .env file: {e}")
                return False
        else:
            logger.error("Neither .env nor sample env file found.")
            return False
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API keys
    required_vars = ["OPENAI_API_KEY", "API_GATEWAY_URL", "API_GATEWAY_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.warning("Application may have limited functionality.")
    
    return True

# This function is no longer used as we moved the port handling to main()
# Keeping it as a stub for backward compatibility
def run_server(host="0.0.0.0", port=5000, debug=False):
    """Run the Flask server."""
    from server import app
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

def open_browser(url, delay=1.0):
    """Open the browser after a short delay."""
    def _open_browser():
        time.sleep(delay)
        webbrowser.open(url)
    
    import threading
    browser_thread = threading.Thread(target=_open_browser)
    browser_thread.daemon = True
    browser_thread.start()

def main():
    """Main function to start the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the P2P Lending Voice AI Assistant Web Application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Please fix the issues and try again.")
        sys.exit(1)
    
    # Create required directories
    Path("static/audio").mkdir(parents=True, exist_ok=True)
    
    # Run the server (this will find an available port if needed)
    from server import app
    import socket
    
    # Try to find an available port if the specified one is in use
    original_port = args.port
    max_attempts = 10
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # Test if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((args.host, args.port))
                break
        except OSError:
            attempts += 1
            args.port += 1
            logger.warning(f"Port {args.port-1} is in use, trying port {args.port}")
    
    if attempts == max_attempts:
        logger.error(f"Could not find an available port after {max_attempts} attempts")
        sys.exit(1)
    
    if args.port != original_port:
        logger.info(f"Using port {args.port} instead of {original_port}")
    
    # Open browser unless disabled
    if not args.no_browser:
        open_browser(f"http://localhost:{args.port}")
    
    # Run the server
    logger.info(f"Starting server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        sys.exit(0) 
        