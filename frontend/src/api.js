import axios from 'axios';

// Use the actual AWS API Gateway URL from config
const API_BASE_URL = 'https://9kti499scf.execute-api.us-west-2.amazonaws.com/dev';

// Create axios instance with common config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// API functions
export const sendTextQuery = async (text, sessionId) => {
  try {
    const response = await apiClient.post('/nlp', {
      operation: 'generate_response',
      text,
      session_id: sessionId
    });
    return response.data;
  } catch (error) {
    console.error('Error sending text query:', error);
    throw error;
  }
};

// For audio transcription, we'd normally send to AWS Transcribe
// but for now, we'll just have the frontend handle it locally
// since that's not the focus of your immediate problem
export const sendAudioForTranscription = async (audioBlob) => {
  try {
    // This would ideally connect to your ASR service
    // but we'll throw an error to indicate this isn't implemented yet
    throw new Error("Speech recognition requires connecting to OpenAI's Whisper API. Use text input for now.");
  } catch (error) {
    console.error('Error with transcription:', error);
    throw error;
  }
};

const api = {
  sendTextQuery,
  sendAudioForTranscription
};

export default api; 