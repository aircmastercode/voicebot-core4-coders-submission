/**
 * Message Component - Renders a single message in the chat
 */
const Message = ({ message, isStreaming }) => {
  const { role, content, audioUrl } = message;
  
  // Determine message class based on role
  const messageClass = role === 'user' ? 'user' : 
                       role === 'system' ? 'system' : 'bot';
  
  // Function to render message content with proper formatting
  const renderContent = () => {
    // If this is a system message, just return the content
    if (role === 'system') {
      return content;
    }
    
    // Split content by newlines to preserve formatting
    const paragraphs = content.split('\n').filter(p => p.trim() !== '');
    
    // If there's only one paragraph, return it directly
    if (paragraphs.length <= 1) {
      return content;
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
    if (isStreaming && role === 'assistant') {
      return <span className="cursor"></span>;
    }
    return null;
  };
  
  return (
    <div className={`message ${messageClass}`}>
      <div className="message-content">
        <div className="streaming-text">
          {renderContent()}
          {renderStreamingCursor()}
        </div>
        {renderAudioPlayer()}
      </div>
    </div>
  );
}; 