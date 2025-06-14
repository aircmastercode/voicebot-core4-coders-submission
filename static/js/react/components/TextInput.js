/**
 * TextInput Component - Handles text input and submission
 */
const TextInput = ({ onSendText, botStatus }) => {
  const [text, setText] = React.useState('');
  const inputRef = React.useRef(null);
  
  // Focus input on mount
  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  // Handle input change
  const handleChange = (e) => {
    setText(e.target.value);
  };
  
  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Don't submit empty text
    if (!text.trim()) return;
    
    // Send the text
    onSendText(text);
    
    // Clear the input
    setText('');
  };
  
  // Handle key press (Enter to submit)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };
  
  // Determine if the input should be disabled
  const isDisabled = botStatus === 'thinking' || botStatus === 'speaking';
  
  return (
    <form className="text-input" onSubmit={handleSubmit}>
      <input
        ref={inputRef}
        type="text"
        placeholder={isDisabled ? 'Please wait...' : 'Type your message...'}
        value={text}
        onChange={handleChange}
        onKeyPress={handleKeyPress}
        disabled={isDisabled}
      />
      <button type="submit" disabled={isDisabled || !text.trim()}>
        <i className="fas fa-paper-plane"></i>
      </button>
    </form>
  );
}; 