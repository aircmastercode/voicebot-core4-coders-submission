import { Conversation } from '@elevenlabs/client';

// DOM Elements
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const connectionStatus = document.getElementById('connectionStatus');
const agentStatus = document.getElementById('agentStatus');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

let conversation;
let chatWebSocket;

// WebSocket URL for chat
const WEBSOCKET_URL = 'wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/';

async function getSignedUrl() {
  const response = await fetch('http://localhost:3001/api/get-signed-url');
  if (!response.ok) {
      throw new Error(`Failed to get signed url: ${response.statusText}`);
  }
  const { signedUrl } = await response.json();
  return signedUrl;
}

// Function to add a message to the chat UI
function addMessage(text, isUser = false) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
    messageElement.textContent = text;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom
}

// Function to send a message via WebSocket
function sendMessageToWebSocket(message) {
    return new Promise((resolve, reject) => {
        if (!chatWebSocket || chatWebSocket.readyState !== WebSocket.OPEN) {
            connectChatWebSocket()
                .then(() => {
                    sendWebSocketMessage();
                })
                .catch(err => {
                    reject('Failed to connect to chat server. Please try again.');
                });
        } else {
            sendWebSocketMessage();
        }

        function sendWebSocketMessage() {
            try {
                // Set up response handler
                chatWebSocket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.response) {
                        resolve(data.response);
                    } else if (data.error) {
                        reject(data.error);
                    }
                };

                // Send the message
                const payload = {
                    action: 'sendMessage',
                    text: message
                };
                chatWebSocket.send(JSON.stringify(payload));
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                reject('Error sending message. Please try again.');
            }
        }
    });
}

// Connect to the chat WebSocket
async function connectChatWebSocket() {
    return new Promise((resolve, reject) => {
        if (chatWebSocket && chatWebSocket.readyState === WebSocket.OPEN) {
            resolve(); // Already connected
            return;
        }
        
        chatWebSocket = new WebSocket(WEBSOCKET_URL);
        
        chatWebSocket.onopen = function() {
            console.log('Chat WebSocket connected');
            resolve();
        };
        
        chatWebSocket.onerror = function(error) {
            console.error('Chat WebSocket error:', error);
            reject(error);
        };
        
        chatWebSocket.onclose = function() {
            console.log('Chat WebSocket closed');
        };
    });
}

// Handle sending a message
async function handleSendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, true);
    messageInput.value = '';

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.classList.add('message', 'bot-message');
    typingIndicator.textContent = 'Typing...';
    chatMessages.appendChild(typingIndicator);

    try {
        // Get response via WebSocket
        const response = await sendMessageToWebSocket(message);

        // Remove typing indicator and add bot response
        chatMessages.removeChild(typingIndicator);
        addMessage(response);
    } catch (error) {
        // Remove typing indicator and show error
        chatMessages.removeChild(typingIndicator);
        addMessage(`Error: ${error}`);
    }
}

async function startConversation() {
    try {
        // Request microphone permission
        await navigator.mediaDevices.getUserMedia({ audio: true });

        const signedUrl = await getSignedUrl();

        // Start the conversation
        conversation = await Conversation.startSession({
            signedUrl,
            onConnect: () => {
                connectionStatus.textContent = 'Connected';
                startButton.disabled = true;
                stopButton.disabled = false;
                
                // Add welcome message
                addMessage('Hello! I am your AI assistant. How can I help you today?');
            },
            onDisconnect: () => {
                connectionStatus.textContent = 'Disconnected';
                startButton.disabled = false;
                stopButton.disabled = true;
            },
            onError: (error) => {
                console.error('Error:', error);
                addMessage('Sorry, there was an error with the voice connection.');
            },
            onModeChange: (mode) => {
                agentStatus.textContent = mode.mode === 'speaking' ? 'speaking' : 'listening';
            },
        });
    } catch (error) {
        console.error('Failed to start conversation:', error);
        addMessage('Failed to start voice conversation. You can still use text chat.');
    }
}

async function stopConversation() {
    if (conversation) {
        await conversation.endSession();
        conversation = null;
        addMessage('Voice conversation ended. You can still use text chat.');
    }
}

// Event Listeners
startButton.addEventListener('click', startConversation);
stopButton.addEventListener('click', stopConversation);
sendButton.addEventListener('click', handleSendMessage);

// Allow sending messages with Enter key
messageInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        handleSendMessage();
    }
});

// Initialize WebSocket connection for chat
connectChatWebSocket().catch(error => {
    console.error('Failed to connect to chat WebSocket:', error);
});

// Initialize with a welcome message
addMessage('Welcome! Click "Start Conversation" to begin voice chat or type a message below to use text chat.');
