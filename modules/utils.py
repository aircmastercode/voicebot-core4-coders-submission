#!/usr/bin/env python3
"""
Utility functions for the P2P Lending Voice AI Assistant.

This module contains common utility functions used across the application.
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def load_config(config_path):
    """Load configuration from YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        sys.exit(1)


def setup_logger(log_level="INFO", log_file="logs/app.log"):
    """Set up logging configuration.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(numeric_level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def resolve_env_vars(config):
    """Resolve environment variables in configuration.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        dict: Configuration with environment variables resolved
    """
    if isinstance(config, dict):
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                config[key] = os.environ.get(env_var, '')
            elif isinstance(value, (dict, list)):
                resolve_env_vars(value)
    elif isinstance(config, list):
        for i, item in enumerate(config):
            if isinstance(item, (dict, list)):
                resolve_env_vars(item)
    
    return config


def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist.
    
    Args:
        directory_path (str): Path to directory
    """
    path = Path(directory_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {directory_path}")


def format_time_ms(milliseconds):
    """Format milliseconds as a human-readable string.
    
    Args:
        milliseconds (float): Time in milliseconds
        
    Returns:
        str: Formatted time string
    """
    if milliseconds < 1000:
        return f"{milliseconds:.2f}ms"
    
    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = seconds / 60
    seconds_remainder = seconds % 60
    return f"{int(minutes)}m {seconds_remainder:.2f}s"