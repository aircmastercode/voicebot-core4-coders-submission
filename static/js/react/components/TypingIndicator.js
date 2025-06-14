/**
 * TypingIndicator Component - Shows when the bot is thinking or generating a response
 */
const TypingIndicator = ({ isVisible }) => {
  // Use state to track when to actually remove the indicator from the DOM
  const [isRendered, setIsRendered] = React.useState(isVisible);
  const [dots, setDots] = React.useState(1);
  
  // Handle visibility changes with a slight delay for fade out
  React.useEffect(() => {
    if (isVisible) {
      setIsRendered(true);
    } else {
      // Small delay before removing from DOM to allow for fade out animation
      const timeout = setTimeout(() => {
        setIsRendered(false);
      }, 200);
      return () => clearTimeout(timeout);
    }
  }, [isVisible]);
  
  // Animate the dots when visible
  React.useEffect(() => {
    let interval;
    if (isVisible) {
      interval = setInterval(() => {
        setDots(prev => (prev % 3) + 1);
      }, 500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isVisible]);
  
  // Don't render anything if not visible and animation has completed
  if (!isRendered) {
    return null;
  }
  
  // Create the dots string
  const dotsString = '.'.repeat(dots);
  
  return (
    <div className={`message bot ${isVisible ? 'typing-visible' : 'typing-hidden'}`}>
      <div className="message-content">
        <div className="typing-indicator">
          <div className="typing-text">Thinking{dotsString}</div>
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}; 