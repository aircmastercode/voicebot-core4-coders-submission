# P2P Lending Voice Assistant Frontend

This is a React-based frontend for the P2P Lending Voice AI Assistant. It provides a modern, user-friendly interface for interacting with the voice assistant.

## Features

- Voice input using the browser's microphone API
- Text input for typing questions directly
- Chat interface with message history
- Text-to-speech for reading responses aloud
- Responsive Material UI design

## Setup Instructions

### Prerequisites

- Node.js 14+ and npm/yarn
- Access to the backend API

### Installation

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Configure the API endpoint:
   - Open `src/api.js`
   - Update `API_BASE_URL` with your backend API URL

### Running the Application

Start the development server:
```bash
npm start
```

This will launch the application at http://localhost:3000

### Building for Production

Create a production build:
```bash
npm run build
```

The build files will be in the `build` directory.

## Usage

1. **Text Input**:
   - Type your question in the text field
   - Click "Send" or press Enter

2. **Voice Input**:
   - Click the microphone icon to start recording
   - Speak your question
   - Click the stop icon (or wait for automatic stop)
   - The system will transcribe your speech and send it to the backend

3. **Listening to Responses**:
   - Click the speaker icon next to any response to have it read aloud

## System Architecture

The frontend communicates with the backend API, which processes requests through:
1. AWS API Gateway
2. AWS Lambda (for NLP processing)
3. AWS Bedrock (Claude AI for responses)
4. S3 (for conversation history)

## Extending the Frontend

To add more features:
- Add new API methods in `src/api.js`
- Expand the UI components in `src/App.js`
- Add additional styling in `src/App.css`

## License

MIT 