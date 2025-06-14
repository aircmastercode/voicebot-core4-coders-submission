/**
 * StatusBar Component - Displays connection and bot status
 */
const StatusBar = ({ connectionStatus, botStatus }) => {
  // Get connection status icon and text
  const getConnectionStatus = () => {
    switch (connectionStatus) {
      case 'connected':
        return { icon: 'fa-circle-check', text: 'Connected', className: 'connected' };
      case 'connecting':
        return { icon: 'fa-circle-notch fa-spin', text: 'Connecting...', className: 'connecting' };
      case 'disconnected':
        return { icon: 'fa-circle-xmark', text: 'Disconnected', className: 'disconnected' };
      case 'error':
        return { icon: 'fa-triangle-exclamation', text: 'Connection Error', className: 'error' };
      default:
        return { icon: 'fa-circle-question', text: 'Unknown', className: '' };
    }
  };
  
  // Get bot status icon and text
  const getBotStatus = () => {
    switch (botStatus) {
      case 'idle':
        return { icon: 'fa-robot', text: 'Ready', className: 'idle' };
      case 'thinking':
        return { icon: 'fa-circle-notch fa-spin', text: 'Thinking...', className: 'thinking' };
      case 'generating':
        return { icon: 'fa-comment-dots', text: 'Generating response...', className: 'generating' };
      case 'speaking':
        return { icon: 'fa-volume-high', text: 'Speaking...', className: 'speaking' };
      default:
        return { icon: 'fa-robot', text: 'Ready', className: 'idle' };
    }
  };
  
  const connectionStatusInfo = getConnectionStatus();
  const botStatusInfo = getBotStatus();
  
  return (
    <div className="status-bar">
      <div className={`connection-status ${connectionStatusInfo.className}`}>
        <i className={`fas ${connectionStatusInfo.icon}`}></i>
        {connectionStatusInfo.text}
      </div>
      <div className={`bot-status ${botStatusInfo.className}`}>
        <i className={`fas ${botStatusInfo.icon}`}></i>
        {botStatusInfo.text}
      </div>
    </div>
  );
}; 