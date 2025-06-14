/**
 * TypingIndicator Component - Shows when the bot is thinking or generating a response
 */
const TypingIndicator = ({ isVisible }) => {
  if (!isVisible) {
    return null;
  }
  
  return (
    <div className="message bot">
      <div className="message-content">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}; 