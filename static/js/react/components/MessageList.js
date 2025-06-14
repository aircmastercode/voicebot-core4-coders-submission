/**
 * MessageList Component - Renders the list of messages in the chat
 */
const MessageList = ({ messages, streamingMessage }) => {
  const messagesEndRef = React.useRef(null);
  
  // Scroll to bottom when messages change
  React.useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);
  
  // Function to scroll to the bottom of the message list
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  return (
    <div className="chat-messages">
      {/* Render all completed messages */}
      {messages.map((message, index) => (
        <Message 
          key={index} 
          message={message} 
          isStreaming={false} 
        />
      ))}
      
      {/* Render the streaming message if there is one */}
      {streamingMessage && (
        <Message 
          message={streamingMessage} 
          isStreaming={true} 
        />
      )}
      
      {/* Empty div for scrolling to bottom */}
      <div ref={messagesEndRef} />
    </div>
  );
}; 