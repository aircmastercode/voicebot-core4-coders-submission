/**
 * Message Component - Renders a single message in the chat
 */
const Message = ({ message, isStreaming }) => {
  const { role, content, audioUrl } = message;
  
  // Determine message class based on role
  const messageClass = role === 'user' ? 'user' : 
                       role === 'system' ? 'system' : 'bot';
  
  // State for typing effect
  const [visibleContent, setVisibleContent] = React.useState(content);
  const [isTypingEffect, setIsTypingEffect] = React.useState(isStreaming);
  const [isTypingPaused, setIsTypingPaused] = React.useState(false);
  const typingSpeedRef = React.useRef(isStreaming ? 15 : 0); // ms per character
  const contentLengthRef = React.useRef(content.length);
  const typingTimeoutRef = React.useRef(null);
  const pauseTimeoutRef = React.useRef(null);
  const lastBatchTimeRef = React.useRef(Date.now());
  const charsTypedInBatchRef = React.useRef(0);
  
  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current);
    };
  }, []);
  
  // Effect to handle content changes and typing animation
  React.useEffect(() => {
    // If not streaming or system message, show full content immediately
    if (!isStreaming || role === 'system' || role === 'user') {
      setVisibleContent(content);
      setIsTypingEffect(false);
      return;
    }
    
    // For streaming bot messages, implement typing effect
    if (content !== visibleContent) {
      // Check if content has changed significantly (new batch received)
      const contentDiff = content.length - contentLengthRef.current;
      contentLengthRef.current = content.length;
      
      // If content is completely different, show it immediately (prediction replaced)
      if (!content.startsWith(visibleContent) && !visibleContent.startsWith(content)) {
        setVisibleContent(content);
        return;
      }
      
      // If we received a significant amount of new content (likely a new batch)
      if (contentDiff > 10) {
        // Calculate time since last batch
        const timeSinceLastBatch = Date.now() - lastBatchTimeRef.current;
        
        // If this is a new batch and not too soon after the previous one
        if (timeSinceLastBatch > 500) {
          // Reset the chars typed counter for the new batch
          charsTypedInBatchRef.current = 0;
          
          // Update the last batch time
          lastBatchTimeRef.current = Date.now();
          
          // Pause briefly before starting to type the new batch
          // This creates a more natural rhythm
          setIsTypingPaused(true);
          
          if (pauseTimeoutRef.current) clearTimeout(pauseTimeoutRef.current);
          pauseTimeoutRef.current = setTimeout(() => {
            setIsTypingPaused(false);
            continueTyping();
          }, 300); // Short pause before starting new batch
          
          return;
        }
      }
      
      // If we're not paused, continue typing
      if (!isTypingPaused) {
        continueTyping();
      }
    }
    
    // Function to continue the typing animation
    function continueTyping() {
      // If content is just slightly longer, animate the difference
      if (content.length > visibleContent.length) {
        // Calculate how many characters to add
        const charsToAdd = Math.min(3, content.length - visibleContent.length);
        charsTypedInBatchRef.current += charsToAdd;
        
        // Adjust typing speed based on batch progress
        // Type faster at the beginning of a batch, slower toward the end
        const batchProgress = Math.min(1, charsTypedInBatchRef.current / 20);
        const baseSpeed = 20 + (batchProgress * 30); // 20ms at start, up to 50ms at end
        
        // Also adjust for punctuation - slow down at periods, commas, etc.
        const nextChar = content.charAt(visibleContent.length);
        const punctuationDelay = /[.,!?;:]/.test(nextChar) ? 200 : 0;
        
        // Schedule the typing effect
        if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = setTimeout(() => {
          // Show more characters
          setVisibleContent(content.substring(0, visibleContent.length + charsToAdd));
        }, baseSpeed + punctuationDelay);
      }
    }
  }, [content, visibleContent, isStreaming, role, isTypingPaused]);
  
  // Function to render message content with proper formatting
  const renderContent = () => {
    // If this is a system message, just return the content
    if (role === 'system') {
      return content;
    }
    
    // Get the content to display (either full content or the currently visible portion)
    const displayContent = isTypingEffect ? visibleContent : content;
    
    // Split content by newlines to preserve formatting
    const paragraphs = displayContent.split('\n').filter(p => p.trim() !== '');
    
    // If there's only one paragraph, return it directly
    if (paragraphs.length <= 1) {
      return displayContent;
    }
    
    // Otherwise, render each paragraph
    return paragraphs.map((paragraph, index) => (
      <p key={index} style={{ marginBottom: index < paragraphs.length - 1 ? '0.5rem' : '0' }}>
        {paragraph}
      </p>
    ));
  };
  
  // Render the audio player button if audio URL is available
  const renderAudioPlayer = () => {
    if (audioUrl && role === 'assistant') {
      return <AudioPlayer audioUrl={audioUrl} />;
    }
    return null;
  };
  
  // Render the cursor for streaming text
  const renderStreamingCursor = () => {
    if (isStreaming && role === 'assistant' && isTypingEffect) {
      return <span className={`cursor ${isTypingPaused ? 'paused' : ''}`}></span>;
    }
    return null;
  };
  
  return (
    <div className={`message ${messageClass}`}>
      <div className="message-content">
        <div className={`streaming-text ${isStreaming ? 'active-streaming' : ''}`}>
          {renderContent()}
          {renderStreamingCursor()}
        </div>
        {renderAudioPlayer()}
      </div>
    </div>
  );
}; 