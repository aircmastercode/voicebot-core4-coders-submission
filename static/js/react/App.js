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
  const [predictedResponse, setPredictedResponse] = React.useState('');
  const [isFirstChunk, setIsFirstChunk] = React.useState(true);
  
  // Refs
  const webSocketRef = React.useRef(null);
  const streamTimeoutRef = React.useRef(null);
  const responseStartTimeRef = React.useRef(null);
  const chunkCountRef = React.useRef(0);
  const lastUserQueryRef = React.useRef('');
  const typingIndicatorTimeoutRef = React.useRef(null);
  
  // Initialize WebSocket on component mount
  React.useEffect(() => {
    // Use pre-established connection if available, or create a new one
    const webSocketService = window.preConnectedWebSocket || new WebSocketService();
    webSocketRef.current = webSocketService;
    
    // Set up WebSocket event handlers
    webSocketService.onStatusChange(setConnectionStatus);
    webSocketService.onMessage(handleWebSocketMessage);
    
    // Connect to WebSocket immediately if not already connected
    if (!window.preConnectedWebSocket) {
      webSocketService.connect();
    } else {
      // Update connection status for pre-established connection
      setConnectionStatus(webSocketService.isConnected ? 'connected' : 'connecting');
    }
    
    // Add welcome message with immediate display
    setTimeout(() => {
      addSystemMessage('Welcome to the P2P Lending Voice AI Assistant! How can I help you today?');
    }, 100);
    
    // Clean up on unmount
    return () => {
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      if (typingIndicatorTimeoutRef.current) {
        clearTimeout(typingIndicatorTimeoutRef.current);
      }
      // Don't disconnect if this is the pre-established connection
      if (!window.preConnectedWebSocket) {
        webSocketService.disconnect();
      }
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
  
  // Generate a predicted response based on the user query
  const generatePredictedResponse = (query) => {
    // Simple prediction based on common P2P lending questions
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('hello') || lowerQuery.includes('hi') || lowerQuery.includes('hey')) {
      return 'Hi there! How can I help you with P2P lending today?';
    }
    
    if (lowerQuery.includes('what is') && lowerQuery.includes('p2p')) {
      return 'P2P lending connects individual lenders with borrowers through online platforms, bypassing traditional banks.';
    }
    
    if (lowerQuery.includes('risk')) {
      return 'P2P lending involves several risks, including credit default risk, platform risk, and liquidity risk.';
    }
    
    if (lowerQuery.includes('benefit') || lowerQuery.includes('advantage')) {
      return 'P2P lending offers potentially higher returns for investors and more favorable rates for borrowers.';
    }
    
    // Default predicted response
    return 'I\'m analyzing your question about P2P lending...';
  };
  
  // Handle WebSocket messages with optimized streaming
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message received:', data);
    
    // Handle streaming response chunks
    if (data.response_chunk !== undefined) {
      // Track chunk count for analytics
      chunkCountRef.current += 1;
      
      // Start timing if this is the first chunk
      if (isFirstChunk && !data.is_fake_chunk) {
        responseStartTimeRef.current = Date.now();
        setIsFirstChunk(false);
      }
      
      // Reset the stream timeout
      if (streamTimeoutRef.current) {
        clearTimeout(streamTimeoutRef.current);
      }
      
      // Set a timeout to finalize the message if no new chunks arrive
      streamTimeoutRef.current = setTimeout(() => {
        finalizeStreamingMessage();
      }, 5000); // Reduced from 8000ms to 5000ms for faster finalization
      
      // If this is the first real chunk, hide the typing indicator
      if (!streamingMessage || data.is_fake_chunk) {
        setShowTypingIndicator(false);
      }
      
      // Handle fake chunks (used for immediate response impression)
      if (data.is_fake_chunk) {
        // Use predicted response for fake chunk
        setStreamingMessage({
          role: 'assistant',
          content: predictedResponse
        });
        return;
      }
      
      // Update or create the streaming message
      setStreamingMessage(prevMessage => {
        // If we have a predicted response and this is a real first chunk,
        // decide whether to keep the prediction or use the real chunk
        if (prevMessage && prevMessage.content === predictedResponse && chunkCountRef.current <= 2) {
          // For the first couple of chunks, blend the prediction with the real content
          // to create a smooth transition and avoid visual "jumping"
          const newChunk = data.response_chunk || '';
          const blendedContent = blendContent(prevMessage.content, newChunk);
          
          return {
            ...prevMessage,
            content: blendedContent
          };
        } else if (prevMessage) {
          // Append to existing message
          const newChunk = data.response_chunk || '';
          return {
            ...prevMessage,
            content: prevMessage.content + newChunk
          };
        } else {
          // Create new message
          return {
            role: 'assistant',
            content: data.response_chunk || ''
          };
        }
      });
    }
    
    // Handle complete response
    if (data.response) {
      // Hide typing indicator
      setShowTypingIndicator(false);
      
      // Log response time for analytics
      if (responseStartTimeRef.current) {
        const responseTime = Date.now() - responseStartTimeRef.current;
        console.log(`Full response received in ${responseTime}ms with ${chunkCountRef.current} chunks`);
      }
      
      // If we have a streaming message, finalize it
      if (streamingMessage) {
        finalizeStreamingMessage(data.audio_url);
      } else {
        // Otherwise, add a new message
        addMessage('assistant', data.response, data.audio_url);
      }
      
      // Reset state for next interaction
      setIsFirstChunk(true);
      chunkCountRef.current = 0;
      responseStartTimeRef.current = null;
      
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
      
      // Reset state for next interaction
      setIsFirstChunk(true);
      chunkCountRef.current = 0;
      responseStartTimeRef.current = null;
      
      // Update bot status
      setBotStatus('idle');
    }
  };
  
  // Blend predicted content with real content for smoother transitions
  const blendContent = (predicted, newChunk) => {
    // If the new chunk is the beginning of a sentence, replace the prediction
    if (newChunk.match(/^[A-Z]/) || newChunk.length > 20) {
      return newChunk;
    }
    
    // Otherwise, append the new chunk to maintain continuity
    return predicted + newChunk;
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
      
      // Reset state for next interaction
      setIsFirstChunk(true);
      chunkCountRef.current = 0;
    }
  };
  
  // Show typing indicator immediately after query submission
  const showTypingIndicatorImmediately = () => {
    // Show typing indicator immediately
    setShowTypingIndicator(true);
    
    // Clear any existing timeout
    if (typingIndicatorTimeoutRef.current) {
      clearTimeout(typingIndicatorTimeoutRef.current);
    }
    
    // Set a fallback timeout to hide the indicator if no response comes
    typingIndicatorTimeoutRef.current = setTimeout(() => {
      if (showTypingIndicator && !streamingMessage) {
        setShowTypingIndicator(false);
      }
    }, 15000); // 15 seconds fallback
  };
  
  // Send a text message
  const handleSendText = (text) => {
    // Don't send empty messages
    if (!text.trim()) return;
    
    // Store the user query for prediction
    lastUserQueryRef.current = text;
    
    // Generate a predicted response
    const predicted = generatePredictedResponse(text);
    setPredictedResponse(predicted);
    
    // Add user message to conversation
    addMessage('user', text);
    
    // Show typing indicator immediately after query submission
    showTypingIndicatorImmediately();
    
    // Update bot status
    setBotStatus('thinking');
    
    // Reset chunk count and timing
    chunkCountRef.current = 0;
    responseStartTimeRef.current = null;
    setIsFirstChunk(true);
    
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
    
    // Show typing indicator immediately after voice submission
    showTypingIndicatorImmediately();
    
    // Update bot status
    setBotStatus('thinking');
    
    // Reset chunk count and timing
    chunkCountRef.current = 0;
    responseStartTimeRef.current = null;
    setIsFirstChunk(true);
    
    // Set a default predicted response for voice input
    setPredictedResponse('I\'m processing your question about P2P lending...');
    
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
          
          // Update the predicted response based on the transcription
          const predicted = generatePredictedResponse(data.text);
          setPredictedResponse(predicted);
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