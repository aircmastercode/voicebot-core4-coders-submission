/**
 * Main App Component - Orchestrates the entire application
 */
const App = () => {
  // State
  const [mode, setMode] = React.useState('text'); // 'text' or 'voice'
  const [messages, setMessages] = React.useState([]);
  const [streamingMessage, setStreamingMessage] = React.useState(null);
  const [isRecording, setIsRecording] = React.useState(false);
  const [connectionStatus, setConnectionStatus] = React.useState('connecting');
  const [botStatus, setBotStatus] = React.useState('idle');
  const [showTypingIndicator, setShowTypingIndicator] = React.useState(false);
  
  // Refs
  const webSocketRef = React.useRef(null);
  const streamTimeoutRef = React.useRef(null);
  
  // Initialize WebSocket on component mount
  React.useEffect(() => {
    // Create WebSocket service
    const webSocketService = new WebSocketService();
    webSocketRef.current = webSocketService;
    
    // Set up WebSocket event handlers
    webSocketService.onStatusChange(setConnectionStatus);
    webSocketService.onMessage(handleWebSocketMessage);
    
    // Connect to WebSocket
    webSocketService.connect();
    
    // Add welcome message
    addSystemMessage('Welcome to the P2P Lending Voice AI Assistant! How can I help you today?');
    
    // Clean up on unmount
    return () => {
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      webSocketService.disconnect();
    };
  }, []);
  
  // Add a message to the conversation
  const addMessage = (role, content, audioUrl = null) => {
    const newMessage = { role, content, audioUrl };
    setMessages(prevMessages => [...prevMessages, newMessage]);
    return newMessage;
  };
  
  // Add a system message
  const addSystemMessage = (content) => {
    addMessage('system', content);
  };
  
  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message received:', data);
    
    // Handle streaming response chunks
    if (data.response_chunk !== undefined) {
      const newChunk = data.response_chunk;
      
      // Reset the stream timeout
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      
      // Set a timeout to finalize the message if no new chunks arrive
      streamTimeoutRef.current = setTimeout(() => {
        finalizeStreamingMessage();
      }, 8000);
      
      // If this is the first chunk, hide the typing indicator
      if (!streamingMessage) {
        setShowTypingIndicator(false);
      }
      
      // Update or create the streaming message
      setStreamingMessage(prevMessage => {
        if (prevMessage) {
          // Append to existing message
          return {
            ...prevMessage,
            content: prevMessage.content + newChunk
          };
        } else {
          // Create new message
          return {
            role: 'assistant',
            content: newChunk
          };
        }
      });
    }
    
    // Handle complete response
    if (data.response) {
      // Hide typing indicator
      setShowTypingIndicator(false);
      
      // If we have a streaming message, finalize it
      if (streamingMessage) {
        finalizeStreamingMessage(data.audio_url);
      } else {
        // Otherwise, add a new message
        addMessage('assistant', data.response, data.audio_url);
      }
      
      // Update bot status
      setBotStatus('idle');
    }
    
    // Handle audio URL updates
    if (data.audio_url && streamingMessage) {
      setStreamingMessage(prevMessage => ({
        ...prevMessage,
        audioUrl: data.audio_url
      }));
    }
    
    // Handle errors
    if (data.error) {
      // Hide typing indicator
      setShowTypingIndicator(false);
      
      // Add error message
      addSystemMessage(`Error: ${data.error}`);
      
      // Update bot status
      setBotStatus('idle');
    }
  };
  
  // Finalize the streaming message
  const finalizeStreamingMessage = (audioUrl = null) => {
    if (streamingMessage) {
      // Add the streaming message to the conversation history
      addMessage('assistant', streamingMessage.content, audioUrl || streamingMessage.audioUrl);
      
      // Clear the streaming message
      setStreamingMessage(null);
      
      // Clear the stream timeout
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
        streamTimeoutRef.current = null;
      }
      
      // Update bot status
      setBotStatus('idle');
    }
  };
  
  // Send a text message
  const handleSendText = (text) => {
    // Don't send empty messages
    if (!text.trim()) return;
    
    // Add user message to conversation
    addMessage('user', text);
    
    // Show typing indicator
    setShowTypingIndicator(true);
    
    // Update bot status
    setBotStatus('thinking');
    
    // Send message to WebSocket
    if (webSocketRef.current) {
      webSocketRef.current.sendMessage({
        text,
        history: messages.filter(msg => msg.role !== 'system')
      });
    }
  };
  
  // Send a voice message
  const handleSendVoice = (audioBlob) => {
    // Create form data
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    formData.append('history', JSON.stringify(messages.filter(msg => msg.role !== 'system')));
    
    // Show typing indicator
    setShowTypingIndicator(true);
    
    // Update bot status
    setBotStatus('thinking');
    
    // Send the audio to the server
    fetch('/api/speech', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        // Add user message with transcription
        if (data.text) {
          addMessage('user', data.text);
        }
        
        // Handle response
        if (data.response) {
          // Hide typing indicator
          setShowTypingIndicator(false);
          
          // Add bot message
          addMessage('assistant', data.response, data.audio_url);
          
          // Update bot status
          setBotStatus('idle');
        } else if (data.error) {
          // Hide typing indicator
          setShowTypingIndicator(false);
          
          // Add error message
          addSystemMessage(`Error: ${data.error}`);
          
          // Update bot status
          setBotStatus('idle');
        }
      })
      .catch(error => {
        console.error('Error sending audio:', error);
        
        // Hide typing indicator
        setShowTypingIndicator(false);
        
        // Add error message
        addSystemMessage('Error sending audio. Please try again.');
        
        // Update bot status
        setBotStatus('idle');
      });
  };
  
  // Switch between text and voice modes
  const switchMode = (newMode) => {
    setMode(newMode);
  };
  
  return (
    <div className="container">
      <header>
        <div className="logo">
          <i className="fas fa-robot"></i>
          <h1>P2P Lending Voice AI Assistant</h1>
        </div>
        <div className="mode-toggle">
          <button 
            className={mode === 'text' ? 'active' : ''} 
            onClick={() => switchMode('text')}
          >
            <i className="fas fa-keyboard"></i>
            Text
          </button>
          <button 
            className={mode === 'voice' ? 'active' : ''} 
            onClick={() => switchMode('voice')}
          >
            <i className="fas fa-microphone"></i>
            Voice
          </button>
        </div>
      </header>
      
      <main>
        <div className="chat-container">
          <MessageList 
            messages={messages} 
            streamingMessage={streamingMessage} 
          />
          {showTypingIndicator && <TypingIndicator isVisible={true} />}
        </div>
        
        <div className="input-container">
          {mode === 'voice' ? (
            <VoiceInput 
              onSendVoice={handleSendVoice} 
              isRecording={isRecording} 
              setIsRecording={setIsRecording} 
              botStatus={botStatus} 
            />
          ) : (
            <TextInput 
              onSendText={handleSendText} 
              botStatus={botStatus} 
            />
          )}
        </div>
      </main>
      
      <StatusBar 
        connectionStatus={connectionStatus} 
        botStatus={botStatus} 
      />
    </div>
  );
}; 