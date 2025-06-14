/**
 * Main entry point for the React application
 * Pre-establishes WebSocket connection for faster initial response
 */

// Pre-establish WebSocket connection before rendering the app
const preConnectWebSocket = () => {
  try {
    // Create a hidden WebSocket connection that will be reused by the app
    window.preConnectedWebSocket = new WebSocketService();
    window.preConnectedWebSocket.connect();
    console.log('Pre-established WebSocket connection');
  } catch (e) {
    console.warn('Failed to pre-establish WebSocket connection:', e);
  }
};

// Try to pre-connect
preConnectWebSocket();

// Render the app
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />); 