# AI-Humanized Voicebot Hackathon: Participant Instructions

# & Guidelines

**Welcome, Innovators!**
We are thrilled to have you participate in this exciting challenge to build the next
generation of conversational AI. Your mission is to build a voice AI assistant that
replicates the fluency, adaptability, and empathy of a human sales representative.
**Problem Statement** : Your mission is to conceptualize and build a state-of-the-art
P2P Lending Awareness & Sales voice bot application. This involves creating a
voice-to-text/voice AI assistant designed to educate potential users about
Peer-to-Peer lending and guide them through the initial sales and onboarding
process. Your solution must effectively replicate the fluency, adaptability, and
empathy of a human sales representative, while adhering to the datasets and
guidelines provided for this hackathon.
This document provides all the necessary instructions and guidelines for the
hackathon. Please read it carefully to understand the competition structure,
submission requirements, and evaluation criteria.

## 1. Hackathon Structure & Timeline

The hackathon is divided into two rounds:
● **Round 1 (Qualification):** An initial filtering round based on a code submission
that will be evaluated against a hidden test dataset.
● **Round 2 (Final Presentation):** Shortlisted teams will present a live demo of their
fully functional voicebot to our panel of judges.
**Key Deadline**
● **Round 1 Submission Deadline: 1:00 PM, Sunday, June 15th.** Late submissions
will not be accepted.
**● Round 2 Evaluation Tentative Time: 2:00 PM to 5.30 PM, Sunday, June 15th**


## 2. Round 1: Qualification & Submission Guidelines

Your goal in Round 1 is to submit a project that meets the minimum functional criteria.
All submissions will be evaluated programmatically.
**2.1. Repository Naming Convention**
Please name your submission repository using the following format:
voicebot_<YourTeamName>_submission
● **Example:** If your team name is "Dynamic Duo", your repository should be named
voicebot_dynamicduo_submission.
**2.2. Required Folder Structure**
To ensure a smooth evaluation process, your project **must** adhere to the following
folder structure. While you can add other modules and dependencies, the core
structure must be maintained.
voicebot_<YourTeamName>_submission/
├── main.py # The main entry point to run your application for the live
demo.
├── run_inference.py # CRUCIAL FOR ROUND 1: The script to generate
responses on test data.
├── requirements.txt # List of all Python dependencies.
├── config/ # Folder for configuration files.
│ └── config.yaml # Centralized config for API keys, model names, or other
parameters.
├── modules/ # Folder for your modular code components.
│ ├── asr_module.py # Logic for Automatic Speech Recognition (Audio-to-Text).
│ ├── nlp_pipeline.py # Logic for Natural Language Processing (intent, entities,
etc.).
│ ├── response_gen.py # Logic for generating or retrieving responses.
│ └── utils.py # Common utility functions.
├── data/ # (Optional) For sample data used during development.
│ └── sample_audio.wav # e.g., an example audio file for testing.
├── output/ # (Optional) For generated logs or intermediate results.
├── README.md # **CRUCIAL!** Must contain clear setup and run
instructions.
└── .env # Store environment variables (API keys, etc.). DO NOT commit
this to Git.


**Mandatory Files:** Your submission **must** include main.py, run_inference.py, and a .env
file with any necessary API keys or secrets.
**2.3. The README.md File**
Your README.md is essential for the judges. It must clearly explain:

1. A brief overview of your project and its key features.
2. Step-by-step instructions on how to set up the environment (e.g., pip install -r
    requirements.txt).
3. How to run the “run_inference.py” file to generate responses for Round 1
4. How to run the live demo using main.py.
5. A list of all API keys or environment variables required in the .env file.
**2.4. Round 1 Evaluation Process**
● The evaluation for Round 1 will be conducted **only** using your **run_inference.py**
script.
● We will run this script against a hidden test dataset (test.csv).
● The test.csv file will contain a Questions column. Your script must read these
questions and generate corresponding answers in a Responses column in the
output file.
● Submissions that successfully process the test data and meet a baseline quality
score will be shortlisted for the final presentation round.


## 3. Round 2: Final Presentation (For Shortlisted Teams)

Congratulations on being shortlisted! This is your opportunity to showcase the full
capabilities of your voicebot. Each team will be allowed a maximum time of 15 mins to
demonstrate their solution.
**3.1. Presentation Format**
● You will be required to give a **live demo** of your working voicebot.
● The core functionality to be demonstrated is **voice input** from a user, processed
by your application, which then returns a **text/voice output**.
● While the primary output is text, demonstrating a human-like **voice output** is a
significant bonus (see "Gaining the Edge" below).
**3.2. Core Technical Evaluation Metrics**
Your project will be judged on its technical merits. Be prepared to speak to how your
solution performs across these five key areas:

1. **Accuracy, Factuality & Relevance:** How correct, truthful, and contextually
    appropriate are the bot's responses?
2. **Human-like Interaction & Conversational Fluency:** How natural, engaging, and
    smooth is the conversation? Does it remember context?
3. **Voice Input Understanding & Processing:** How well does it handle different
    voices, interruptions, and ambiguity?
4. **System Performance & Latency:** How fast and responsive is the bot?
5. **Innovation, Robustness & Ethical AI:** What makes your bot unique? How does it
    handle errors and ensure safe, unbiased interaction?


## 4. Gaining the Edge: Advanced Features for Bonus Recognition

To truly stand out, consider incorporating advanced features. Excelling in these areas
will significantly impress the judges and can be the tiebreaker between great and
winning solutions.
● **Hyper-Realistic Voice Synthesis:** Go beyond standard text-to-speech.
Implement a voice output that is emotionally resonant, with natural pacing and
intonation.
● **Near-Zero Latency Interaction:** Optimize your pipeline for a near-real-time
conversational experience, where the bot's response feels immediate.
● **Seamless Multilingual Dexterity:** Demonstrate the ability to understand and
respond even if the user switches between languages (e.g., Hinglish)
mid-conversation, including robust interruption handling.
● **Advanced Acoustic Clarity Engine:** Implement superior background noise
cancellation and dereverberation to ensure the bot can understand the user
clearly in non-ideal environments.
● **Conversational Nuance Simulation:** Incorporate micro-interactions like
discourse markers ("Hmm, let me see...", "Okay, got it.") to mimic human-like
conversational flow.
● **Strategic Prompt Architecture:** Showcase sophisticated and effective prompt
engineering techniques that elicit the best possible responses from the
underlying language model.
● **Optimized LLM Resource Management:** Demonstrate efficient LLM token
consumption and usage, proving your solution is not only smart but also
cost-effective and scalable.
● **Deep Contextual Memory:** Build a bot that not only remembers the last turn but
can recall details and context from much earlier in the conversation to provide
highly personalized responses.
● **Proactive Conversational Guidance:** Design a bot that doesn't just answer
questions but proactively suggests next steps, related products, or helpful
information, guiding the user like an expert sales associate.
● **Elegant Error & Ambiguity Resolution:** Instead of just saying "I don't
understand," your bot should have graceful fallback mechanisms, ask clarifying
questions, and effectively navigate ambiguity.
Good luck, and we look forward to seeing your incredible creations!


