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
    
    // Enhanced chunk handling
    this.chunkBuffer = [];
    this.batchBuffer = [];
    this.isProcessingChunks = false;
    this.chunkProcessInterval = null;
    this.lastChunkTime = 0;
    this.chunkDelay = 10; // milliseconds between chunk processing
    this.batchSize = 5; // number of chunks to process in a batch (increased from 3)
    this.batchPauseTime = 800; // milliseconds to pause between batches (reduced from 1000)
    this.isProcessingBatch = false;
    this.fakeChunkSent = false;
    this.currentBatchIndex = 0;
    
    // Adaptive batch parameters
    this.minBatchSize = 3;
    this.maxBatchSize = 8;
    this.minPauseTime = 600;
    this.maxPauseTime = 1200;
    this.batchCount = 0;
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
      // Pre-establish connection before user interaction for faster response
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = (event) => {
        console.log("WebSocket connection established");
        this.isConnected = true;
        this.connectionAttempts = 0;
        this._updateStatus("connected");
        
        // Send a ping to keep the connection warm
        this._keepConnectionWarm();
        
        if (this.onOpenCallback) this.onOpenCallback(event);
      };
      
      this.socket.onmessage = (event) => {
        // Process messages immediately to reduce latency
        this._handleMessage(event);
      };
      
      this.socket.onclose = (event) => {
        console.log("WebSocket connection closed", event);
        this.isConnected = false;
        this._updateStatus("disconnected");
        
        // Clear any ongoing chunk processing
        this._clearChunkProcessing();
        
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
   * Keep the connection warm with periodic pings
   */
  _keepConnectionWarm() {
    // Send a ping every 30 seconds to keep the connection alive
    setInterval(() => {
      if (this.isConnected) {
        try {
          this.socket.send(JSON.stringify({ action: "ping" }));
        } catch (e) {
          // Ignore errors during ping
        }
      }
    }, 30000);
  }

  /**
   * Clear chunk processing state
   */
  _clearChunkProcessing() {
    this.chunkBuffer = [];
    this.batchBuffer = [];
    this.isProcessingChunks = false;
    this.isProcessingBatch = false;
    this.fakeChunkSent = false;
    this.currentBatchIndex = 0;
    
    if (this.chunkProcessInterval) {
      clearInterval(this.chunkProcessInterval);
      this.chunkProcessInterval = null;
    }
    
    // Clear any pending timeouts
    if (this.batchTimeoutRef) {
      clearTimeout(this.batchTimeoutRef);
      this.batchTimeoutRef = null;
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
    this._clearChunkProcessing();
    
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
      
      // Reset chunk processing state before sending a new message
      this._clearChunkProcessing();
      
      // Reset fake chunk flag
      this.fakeChunkSent = false;
      
      // Send a fake immediate first chunk to reduce perceived latency
      // This will be replaced by the actual first chunk when it arrives
      setTimeout(() => {
        if (this.onMessageCallback && !this.isProcessingChunks && !this.fakeChunkSent) {
          // Only send the fake chunk if we haven't received a real one yet
          this.fakeChunkSent = true;
          this.onMessageCallback({
            response_chunk: "",
            is_fake_chunk: true,
            session_id: this.sessionId
          });
        }
      }, 800); // Increased delay to allow typing indicator to be visible longer
      
      // Send the actual message
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
        
        // Handle streaming chunk
        this._handleStreamingChunk(data);
      } else if (data.response) {
        this._updateStatus("idle");
        
        // Handle complete response
        this._clearChunkProcessing();
        
        // Pass the message to the callback
        if (this.onMessageCallback) {
          this.onMessageCallback(data);
        }
      } else if (data.error) {
        this._updateStatus("error");
        
        // Clear chunk processing on error
        this._clearChunkProcessing();
        
        // Pass the error to the callback
        if (this.onMessageCallback) {
          this.onMessageCallback(data);
        }
      } else {
        // Pass other messages directly to the callback
        if (this.onMessageCallback) {
          this.onMessageCallback(data);
        }
      }
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  }
  
  /**
   * Handle streaming chunks with optimized delivery
   * @param {Object} data - The chunk data
   */
  _handleStreamingChunk(data) {
    // Set flag to indicate we're receiving real chunks
    this.isProcessingChunks = true;
    this.lastChunkTime = Date.now();
    
    // If this is a real chunk, mark that we've received real data
    if (!data.is_fake_chunk) {
      this.fakeChunkSent = true;
    }
    
    // Add the chunk to the buffer
    this.chunkBuffer.push(data);
    
    // If we're not currently processing a batch, start processing
    if (!this.isProcessingBatch) {
      this._processBatchedChunks();
    }
  }
  
  /**
   * Process chunks in batches with pauses between batches
   */
  _processBatchedChunks() {
    // Set flag to indicate we're processing a batch
    this.isProcessingBatch = true;
    
    // Increment batch counter
    this.batchCount++;
    
    // Adjust batch parameters based on batch count
    // As the conversation progresses, we'll dynamically adjust the batch size and pause time
    // to create a more natural rhythm
    if (this.batchCount > 1) {
      // Vary batch size slightly for a more natural feel
      const randomVariation = Math.random() * 2 - 1; // Random value between -1 and 1
      this.batchSize = Math.max(
        this.minBatchSize,
        Math.min(
          this.maxBatchSize,
          Math.floor(5 + randomVariation)
        )
      );
      
      // Vary pause time as well
      const pauseVariation = Math.random() * 300 - 150; // Random value between -150 and 150
      this.batchPauseTime = Math.max(
        this.minPauseTime,
        Math.min(
          this.maxPauseTime,
          800 + pauseVariation
        )
      );
      
      // For sentences that end with periods, increase pause time
      if (this.lastSentenceEnded) {
        this.batchPauseTime += 200;
        this.lastSentenceEnded = false;
      }
    }
    
    // Create a new batch from the buffer
    const currentBatch = [];
    const batchSize = Math.min(this.batchSize, this.chunkBuffer.length);
    
    // Take chunks from the buffer to create a batch
    for (let i = 0; i < batchSize; i++) {
      if (this.chunkBuffer.length > 0) {
        const chunk = this.chunkBuffer.shift();
        currentBatch.push(chunk);
        
        // Check if this chunk ends with a period, question mark, or exclamation point
        if (chunk.response_chunk && /[.!?]$/.test(chunk.response_chunk.trim())) {
          this.lastSentenceEnded = true;
        }
      }
    }
    
    // If we have chunks in the current batch, process them
    if (currentBatch.length > 0) {
      // Process each chunk in the batch immediately
      currentBatch.forEach(chunk => {
        if (this.onMessageCallback) {
          this.onMessageCallback(chunk);
        }
      });
      
      // If there are more chunks in the buffer, schedule the next batch
      if (this.chunkBuffer.length > 0) {
        this.batchTimeoutRef = setTimeout(() => {
          this._processBatchedChunks();
        }, this.batchPauseTime);
      } else {
        // No more chunks, set flag to indicate we're done processing
        this.isProcessingBatch = false;
        
        // Check again after a short delay in case more chunks arrive
        this.batchTimeoutRef = setTimeout(() => {
          if (this.chunkBuffer.length > 0) {
            this._processBatchedChunks();
          }
        }, 500);
      }
    } else {
      // No chunks in the batch, set flag to indicate we're done processing
      this.isProcessingBatch = false;
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