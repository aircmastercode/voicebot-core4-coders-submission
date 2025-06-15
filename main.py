#!/usr/bin/env python3
"""
P2P Lending Awareness & Sales Voice AI Assistant

Main entry point for the voice assistant application.
This script initializes all components and starts the interactive voice interface.
"""

import os
import sys
import argparse
import yaml
import logging
import time
import asyncio
import sounddevice as sd
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the Python path
sys.path.append('.')

from modules.asr_module import ASRModule, ASRConfig
from modules.tts_module import TTSModule, TTSConfig
from modules.nlp_pipeline import NLPPipeline, NLPConfig
from modules.response_gen import ResponseGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Audio configuration
SAMPLE_RATE = 16000  # ElevenLabs STT expects 16kHz
CHANNELS = 1
BLOCK_SIZE = 1024 # Audio chunk size

async def live_demo(voice_mode=True):
    """
    Starts an interactive, real-time demo of the voicebot.
    
    Args:
        voice_mode: If True, use voice input/output. If False, use text input/output.
    """
    logging.info(f"Starting live demo (voice_mode={voice_mode})...")

    # 1. Initialize modules
    try:
        logging.info("Loading configuration...")
        nlp_config = NLPConfig.from_yaml()
        asr_config = ASRConfig.from_yaml()
        tts_config = TTSConfig.from_yaml()
        
        logging.info("Initializing NLP Pipeline...")
        nlp_pipeline = NLPPipeline(config=nlp_config)
        
        logging.info("Initializing Response Generator...")
        response_generator = ResponseGenerator()
        
        if voice_mode:
            logging.info("Initializing ASR Module...")
            asr_module = ASRModule(config=asr_config)
            
            logging.info("Initializing TTS Module...")
            tts_module = TTSModule(config=tts_config)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Failed to initialize modules: {e}")
        print(f"Error: Could not start the demo. Details: {e}")
        return

    # 2. Start interactive loop
    print("\n--- P2P Lending Voicebot Demo ---")
    print("Ask me anything about Peer-to-Peer lending.")
    if voice_mode:
        print("Speak to interact, or say 'exit' to end the session.")
        print("Type 'text' to switch to text mode.")
    else:
        print("Type your questions, or 'exit' to end the session.")
        print("Type 'voice' to switch to voice mode.")
    print()
    
    session_id = "live-demo-session"
    conversation_history = [] # List to store the conversation turns
    
    # Welcome message
    welcome_message = "Hello! I'm your P2P Lending Assistant. How can I help you today?"
    print(f"Bot: {welcome_message}")
    if voice_mode:
        # Stream welcome message audio
        async def welcome_text_gen():
            yield welcome_message
        async for chunk in tts_module.stream_text_to_speech(welcome_text_gen()):
            # Play audio chunk (requires a separate audio playback mechanism)
            # For now, we'll just pass, but in a real app, this would go to an audio output stream
            # Ensure the chunk size is a multiple of 2 (for int16) to avoid ValueError
            if len(chunk) % 2 != 0:
                chunk += b'\0' # Pad with a zero byte
            sd.play(np.frombuffer(chunk, dtype=np.int16), SAMPLE_RATE)
            sd.wait()
    
    current_mode = "voice" if voice_mode else "text"

    while True:
        try:
            if current_mode == "voice":
                print("\n[Listening...] (Say something or type 'text' to switch modes)")
                # Use a queue to pass audio chunks from the callback to the ASR stream
                audio_queue = asyncio.Queue()
                transcription_buffer = []

                def audio_callback(indata, frames, time, status):
                    if status:
                        logging.warning(f"SoundDevice warning: {status}")
                    audio_queue.put_nowait(np.frombuffer(indata, dtype=np.int16).tobytes())

                def on_transcription_update(transcript: str):
                    # This callback will be called with partial and final transcriptions
                    # For simplicity, we'll just update a buffer and print the latest
                    transcription_buffer.clear()
                    transcription_buffer.append(transcript)
                    print(f"\r[Listening...] (You): {transcript}", end="", flush=True)

                print("\n[Listening...] (Speak now or type 'text' to switch modes)")
                # Start streaming audio from microphone to ASR module
                with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, 
                                       channels=CHANNELS, dtype='int16', 
                                       callback=audio_callback):
                    
                    # Create an async generator for the audio stream from the queue
                    async def audio_stream_generator():
                        while True:
                            chunk = await audio_queue.get()
                            if chunk is None: # Sentinel for end of stream
                                break
                            yield chunk

                    # Run STT in the background
                    stt_task = asyncio.create_task(
                        asr_module.stream_speech_to_text(audio_stream_generator(), on_transcription_update)
                    )

                    # Wait for user to type 'text' or 'exit', or for a significant pause in speech
                    # For a real voicebot, this would be more sophisticated (e.g., VAD)
                    # For now, let's assume a simple text-based trigger to stop listening
                    # or a fixed duration for listening.
                    # This part needs careful design for a smooth UX.
                    
                    # For demonstration, let's just wait for a short period or a specific input
                    # A better approach would be Voice Activity Detection (VAD)
                    user_input_text = await asyncio.to_thread(input) # Non-blocking input
                    if user_input_text.lower() == "text":
                        current_mode = "text"
                        switch_msg = "Switching to text input mode."
                        print(f"\nBot: {switch_msg}")
                        audio_queue.put_nowait(None) # Signal end of audio stream
                        await stt_task # Wait for STT to finish processing remaining audio
                        continue
                    elif user_input_text.lower() in ["exit", "quit"]:
                        audio_queue.put_nowait(None) # Signal end of audio stream
                        await stt_task
                        raise KeyboardInterrupt # Exit the loop
                    
                    # If user typed something else, assume it's a command to stop listening
                    # and process the current transcription
                    audio_queue.put_nowait(None) # Signal end of audio stream
                    await stt_task # Wait for STT to finish processing remaining audio
                    user_query = " ".join(transcription_buffer).strip()
                    print("\n", end="") # Clear the transcription line
                    if not user_query:
                        print("Bot: I didn't catch that. Please try again.")
                        continue
                print(f"You said: {user_query}")
            else:
                user_query = input("You: ")
                
            # Handle mode switching
            if current_mode == "voice" and user_query.lower() == "text":
                current_mode = "text"
                switch_msg = "Switching to text input mode."
                print(f"Bot: {switch_msg}")
                continue
            elif current_mode == "text" and user_query.lower() == "voice":
                current_mode = "voice"
                switch_msg = "Switching to voice input mode."
                print(f"Bot: {switch_msg}")
                continue
                
            # Handle exit commands
            if user_query.lower() in ["exit", "quit"]:
                goodbye_msg = "Goodbye! Thank you for using our P2P Lending Assistant."
                print(f"Bot: {goodbye_msg}")
                if current_mode == "voice":
                    async def goodbye_text_gen():
                        yield goodbye_msg
                    async for chunk in tts_module.stream_text_to_speech(goodbye_text_gen()):
                        sd.play(np.frombuffer(chunk, dtype=np.int16), SAMPLE_RATE)
                        sd.wait()
                break
            
            if not user_query.strip():
                continue

            # Append user message to history
            conversation_history.append({"role": "user", "content": user_query})

            # The pipeline now needs the full history
            nlp_data = nlp_pipeline.process_input(
                user_query, 
                session_id=session_id,
                history=conversation_history
            )
            
            # Step 2: Generate the final response
            final_response = response_generator.get_final_answer(nlp_data)

            # Append bot message to history
            conversation_history.append({"role": "assistant", "content": final_response})
            
            print(f"Bot: {final_response}")
            
            # If in voice mode, speak the response
            if current_mode == "voice":
                async def response_text_gen():
                    yield final_response
                async for chunk in tts_module.stream_text_to_speech(response_text_gen()):
                    sd.play(np.frombuffer(chunk, dtype=np.int16), SAMPLE_RATE)
                    sd.wait()

        except KeyboardInterrupt:
            print("\nBot: Goodbye!")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during the demo loop: {e}", exc_info=True)
            error_msg = "I'm sorry, an unexpected error occurred. Please try again."
            print(f"Bot: {error_msg}")
            if current_mode == "voice":
                try:
                    async def error_text_gen():
                        yield error_msg
                    async for chunk in tts_module.stream_text_to_speech(error_text_gen()):
                        sd.play(np.frombuffer(chunk, dtype=np.int16), SAMPLE_RATE)
                        sd.wait()
                except Exception as tts_e:
                    logging.error(f"Error playing error message: {tts_e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the P2P Lending Voice AI Assistant demo.")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["text", "voice"],
        default="voice", 
        help="The mode to run the demo in: 'text' for text-only or 'voice' for voice interaction."
    )
    
    args = parser.parse_args()
    voice_mode = args.mode == "voice"
    
    asyncio.run(live_demo(voice_mode=voice_mode))