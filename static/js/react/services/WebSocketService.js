/**
 * WebSocketService - Handles WebSocket connections and message processing
 */
class WebSocketService {
  constructor(url) {
    this.url = url || "wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/";
    this.socket = null;
    this.isConnected = false;
    this.sessionId = null;
    this.onMessageCallback = null;
    this.onOpenCallback = null;
    this.onCloseCallback = null;
    this.onErrorCallback = null;
    this.onStatusChangeCallback = null;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 3;
    this.reconnectTimeout = null;
  }

  /**
   * Connect to the WebSocket server
   */
  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
      console.log("WebSocket already connected or connecting");
      return;
    }

    this._updateStatus("connecting");
    
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = (event) => {
        console.log("WebSocket connection established");
        this.isConnected = true;
        this.connectionAttempts = 0;
        this._updateStatus("connected");
        if (this.onOpenCallback) this.onOpenCallback(event);
      };
      
      this.socket.onmessage = (event) => {
        this._handleMessage(event);
      };
      
      this.socket.onclose = (event) => {
        console.log("WebSocket connection closed", event);
        this.isConnected = false;
        this._updateStatus("disconnected");
        if (this.onCloseCallback) this.onCloseCallback(event);
        
        // Try to reconnect if not closed intentionally
        if (!event.wasClean && this.connectionAttempts < this.maxConnectionAttempts) {
          this._reconnect();
        }
      };
      
      this.socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        this._updateStatus("error");
        if (this.onErrorCallback) this.onErrorCallback(error);
      };
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      this._updateStatus("error");
    }
  }

  /**
   * Reconnect to the WebSocket server after a delay
   */
  _reconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    this.connectionAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.connectionAttempts - 1), 10000);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.connectionAttempts}/${this.maxConnectionAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log("Reconnecting to WebSocket...");
      this.connect();
    }, delay);
  }

  /**
   * Close the WebSocket connection
   */
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
      this._updateStatus("disconnected");
    }
  }

  /**
   * Send a message to the WebSocket server
   * @param {Object} message - The message to send
   */
  sendMessage(message) {
    if (!this.isConnected) {
      console.warn("WebSocket is not connected. Attempting to connect...");
      this.connect();
      
      // Queue the message to be sent once connected
      setTimeout(() => this.sendMessage(message), 1000);
      return;
    }
    
    try {
      // Format the message according to the required structure
      const formattedMessage = {
        action: "sendMessage",
        text: message.text
      };
      
      // Include session ID if available
      if (this.sessionId) {
        formattedMessage.session_id = this.sessionId;
      }
      
      // Include history if provided
      if (message.history) {
        formattedMessage.history = message.history;
      }
      
      console.log("Sending message:", formattedMessage);
      this.socket.send(JSON.stringify(formattedMessage));
      
      // Update status to indicate we're waiting for a response
      this._updateStatus("thinking");
    } catch (error) {
      console.error("Error sending message:", error);
      this._updateStatus("error");
    }
  }

  /**
   * Handle incoming WebSocket messages
   * @param {MessageEvent} event - The WebSocket message event
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data);
      
      // Save session ID if provided
      if (data.session_id && !this.sessionId) {
        this.sessionId = data.session_id;
        console.log("Session ID set:", this.sessionId);
      }
      
      // Update status based on message content
      if (data.response_chunk !== undefined) {
        this._updateStatus("generating");
      } else if (data.response) {
        this._updateStatus("idle");
      } else if (data.error) {
        this._updateStatus("error");
      }
      
      // Pass the message to the callback
      if (this.onMessageCallback) {
        this.onMessageCallback(data);
      }
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  }

  /**
   * Update the connection status and notify listeners
   * @param {string} status - The new status
   */
  _updateStatus(status) {
    if (this.onStatusChangeCallback) {
      this.onStatusChangeCallback(status);
    }
  }

  /**
   * Set callback for WebSocket messages
   * @param {Function} callback - The callback function
   */
  onMessage(callback) {
    this.onMessageCallback = callback;
  }

  /**
   * Set callback for WebSocket open event
   * @param {Function} callback - The callback function
   */
  onOpen(callback) {
    this.onOpenCallback = callback;
  }

  /**
   * Set callback for WebSocket close event
   * @param {Function} callback - The callback function
   */
  onClose(callback) {
    this.onCloseCallback = callback;
  }

  /**
   * Set callback for WebSocket error event
   * @param {Function} callback - The callback function
   */
  onError(callback) {
    this.onErrorCallback = callback;
  }

  /**
   * Set callback for status changes
   * @param {Function} callback - The callback function
   */
  onStatusChange(callback) {
    this.onStatusChangeCallback = callback;
  }

  /**
   * Get the current WebSocket connection status
   * @returns {boolean} - Whether the WebSocket is connected
   */
  getConnectionStatus() {
    return this.isConnected;
  }

  /**
   * Get the current session ID
   * @returns {string|null} - The session ID, or null if not set
   */
  getSessionId() {
    return this.sessionId;
  }
} 