import React, { useState, useRef, useEffect } from 'react';
import { 
  Container, Typography, Button, Paper, Box, CircularProgress, 
  TextField, AppBar, Toolbar, IconButton, Alert, Snackbar
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import { sendTextQuery } from './api';
import './App.css';

function App() {
  const [inputText, setInputText] = useState('');
  // eslint-disable-next-line no-unused-vars
  const [responseText, setResponseText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);
  
  const conversationEndRef = useRef(null);

  // Initialize session ID
  useEffect(() => {
    const newSessionId = `session-${Date.now()}`;
    setSessionId(newSessionId);
    
    // Add welcome message to conversation
    setConversation([{
      role: 'assistant',
      content: "Hello! I'm your P2P Lending Assistant. How can I help you today?"
    }]);
  }, []);

  // Scroll to bottom of conversation
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  // Send text to backend
  const sendTextToBackend = async (text) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Add user message to conversation
      const userMessage = { role: 'user', content: text };
      setConversation(prev => [...prev, userMessage]);
      
      try {
        // Call AWS API Gateway directly
        const data = await sendTextQuery(text, sessionId);
        
        if (data && data.response) {
          setResponseText(data.response);
          
          // Add bot response to conversation
          const botMessage = { role: 'assistant', content: data.response };
          setConversation(prev => [...prev, botMessage]);
        } else {
          throw new Error("Invalid response format");
        }
      } catch (err) {
        console.error("API error:", err);
        
        if (err.message.includes('Network Error')) {
          setError("Failed to connect to API Gateway. Please check your internet connection and API configuration.");
        } else if (err.response && err.response.status === 403) {
          setError("Access denied. Please check your API key and permissions.");
        } else {
          setError(`Failed to get response: ${err.message}. Check your API Gateway configuration.`);
        }
      }
    } finally {
      setIsLoading(false);
      setInputText('');
    }
  };

  // Handle text input submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim()) {
      sendTextToBackend(inputText);
    }
  };

  // Speak response using browser's speech synthesis
  const speakResponse = (text) => {
    if ('speechSynthesis' in window) {
      setIsPlaying(true);
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onend = () => setIsPlaying(false);
      
      // Stop any ongoing speech
      window.speechSynthesis.cancel();
      
      // Speak the new text
      window.speechSynthesis.speak(utterance);
    } else {
      setError("Speech synthesis not supported in this browser");
    }
  };

  // Stop speaking
  // eslint-disable-next-line no-unused-vars
  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    }
  };

  // Clear error message
  const handleCloseError = () => {
    setError(null);
  };

  return (
    <div className="App">
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            P2P Lending Voice Assistant
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Container maxWidth="md" sx={{ my: 4 }}>
        <Paper 
          elevation={3} 
          sx={{ 
            p: 3, 
            mb: 2, 
            maxHeight: '60vh', 
            overflow: 'auto',
            bgcolor: '#f9f9f9'
          }}
        >
          {conversation.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 10 }}>
              <Typography variant="h6" color="textSecondary">
                Start the conversation by typing your question
              </Typography>
            </Box>
          ) : (
            conversation.map((msg, index) => (
              <Box 
                key={index} 
                sx={{
                  mb: 2,
                  p: 2,
                  borderRadius: 2,
                  maxWidth: '80%',
                  ml: msg.role === 'user' ? 'auto' : 0,
                  mr: msg.role === 'assistant' ? 'auto' : 0,
                  bgcolor: msg.role === 'user' ? '#1976d2' : '#e0e0e0',
                  color: msg.role === 'user' ? 'white' : 'black',
                }}
              >
                <Typography variant="body1">
                  {msg.content}
                </Typography>
                
                {msg.role === 'assistant' && (
                  <IconButton 
                    size="small" 
                    onClick={() => speakResponse(msg.content)}
                    sx={{ mt: 1, color: isPlaying ? 'primary.main' : 'text.secondary' }}
                  >
                    <VolumeUpIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            ))
          )}
          <div ref={conversationEndRef} />
        </Paper>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', width: '100%', py: 2 }}>
              <CircularProgress />
            </Box>
          ) : (
            <form onSubmit={handleSubmit} style={{ width: '100%', display: 'flex' }}>
              <TextField
                fullWidth
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your message here..."
                variant="outlined"
                disabled={isLoading}
                sx={{ mr: 1 }}
              />
              <Button 
                type="submit" 
                variant="contained" 
                color="primary" 
                disabled={!inputText.trim() || isLoading}
                endIcon={<SendIcon />}
              >
                Send
              </Button>
            </form>
          )}
        </Box>
        
        <Box sx={{ mt: 4, p: 2, bgcolor: '#e8f4fd', borderRadius: 1 }}>
          <Typography variant="body2" color="textSecondary">
            <strong>Connection status:</strong> The frontend is configured to connect directly 
            to AWS API Gateway. Voice input is temporarily disabled.
          </Typography>
        </Box>
      </Container>
    </div>
  );
}

export default App; 