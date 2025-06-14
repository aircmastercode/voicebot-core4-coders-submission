// P2P Lending Voice AI Assistant - Frontend JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const micBtn = document.getElementById('mic-btn');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const voiceInput = document.getElementById('voice-input');
    const textInput = document.getElementById('text-input');
    const voiceModeBtn = document.getElementById('voice-mode-btn');
    const textModeBtn = document.getElementById('text-mode-btn');
    const chatMessages = document.getElementById('chat-messages');
    const voiceStatusText = document.getElementById('voice-status-text');
    const voiceWaves = document.getElementById('voice-waves');
    const connectionStatus = document.getElementById('connection-status');
    const botStatus = document.getElementById('bot-status');
    const errorModal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    const closeErrorBtn = document.getElementById('close-error-btn');

    // API endpoint
    const API_ENDPOINT = '/api';
    // WebSocket endpoint
    const WS_ENDPOINT = 'wss://jiehdal92f.execute-api.us-west-2.amazonaws.com/devx/';

    // State
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let mode = 'voice';
    let conversationHistory = [];
    let isConnected = false;
    let ws = null;
    let sessionId = null;
    let currentStreamingMessage = null; // Track the current streaming message element
    let accumulatedResponse = ''; // Accumulate streaming response chunks
    let currentTypingAnimation = null; // Track the current typing animation timeout

    // Initialize the application
    function init() {
        // Set up event listeners
        micBtn.addEventListener('click', toggleRecording);
        sendBtn.addEventListener('click', sendTextMessage);
        userInput.addEventListener('keypress', handleKeyPress);
        voiceModeBtn.addEventListener('click', switchToVoiceMode);
        textModeBtn.addEventListener('click', switchToTextMode);
        closeErrorBtn.addEventListener('click', closeErrorModal);

        // Check browser support for audio recording
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            console.log('Media devices supported');
            botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Idle</span>';
            botStatus.className = 'idle';
        } else {
            console.warn('Media devices not supported');
            switchToTextMode();
        }

        // Add the welcome message to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: 'Hello! I\'m your P2P Lending Assistant. How can I help you today?'
        });

        // Initialize WebSocket connection
        connectWebSocket();
    }

    // Connect to WebSocket
    function connectWebSocket() {
        try {
            updateConnectionStatus('connecting');
            
            ws = new WebSocket(WS_ENDPOINT);
            
            ws.onopen = () => {
                console.log('WebSocket connection established');
                updateConnectionStatus('connected');
                isConnected = true;
            };
            
            ws.onmessage = (event) => {
                handleWebSocketMessage(event);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateConnectionStatus('error');
                isConnected = false;
            };
            
            ws.onclose = () => {
                console.log('WebSocket connection closed');
                updateConnectionStatus('disconnected');
                isConnected = false;
                
                // Attempt to reconnect after a delay
                setTimeout(() => {
                    if (!isConnected) {
                        connectWebSocket();
                    }
                }, 5000);
            };
        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
            updateConnectionStatus('error');
            isConnected = false;
        }
    }

    // Handle WebSocket messages
    function handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            // Check if this is a streaming response chunk
            if (data.response_chunk !== undefined) {
                // Remove the standalone typing indicator when we start receiving chunks
                removeTypingIndicator();
                
                // If this is the first chunk, create a new message
                if (!currentStreamingMessage) {
                    // Create a new bot message element
                    currentStreamingMessage = document.createElement('div');
                    currentStreamingMessage.className = 'message bot';
                    currentStreamingMessage.innerHTML = `
                        <div class="message-content">
                            <div id="streaming-message"></div>
                        </div>
                    `;
                    chatMessages.appendChild(currentStreamingMessage);
                    
                    // Reset the accumulated response
                    accumulatedResponse = '';
                    
                    // Update bot status to show it's generating text
                    updateBotStatus('generating');
                }
                
                // Append the new chunk to the accumulated response
                const newChunk = data.response_chunk;
                accumulatedResponse += newChunk;
                
                // Update the message content immediately with the new chunk
                const streamingMessageElement = currentStreamingMessage.querySelector('#streaming-message');
                
                // Display the chunk immediately
                if (streamingMessageElement.innerHTML === '') {
                    // First chunk
                    streamingMessageElement.innerHTML = formatBotResponse(newChunk);
                } else {
                    // Append to existing content
                    streamingMessageElement.innerHTML = formatBotResponse(accumulatedResponse);
                }
                
                // Scroll to the bottom as new content arrives
                scrollToBottom();
                
                // Save session ID if provided
                if (data.session_id && !sessionId) {
                    sessionId = data.session_id;
                    console.log('Session ID set:', sessionId);
                }
            }
            // Handle complete response (non-streaming)
            else if (data.response) {
                // Remove the standalone typing indicator
                removeTypingIndicator();
                
                // If we were in streaming mode, finalize the streaming message
                if (currentStreamingMessage) {
                    // Add the complete response to conversation history
                    conversationHistory.push({
                        role: 'assistant',
                        content: accumulatedResponse
                    });
                    
                    // Reset streaming state
                    currentStreamingMessage = null;
                    accumulatedResponse = '';
                    
                    // Play audio response if available and in voice mode
                    if (mode === 'voice' && data.audio_url) {
                        updateBotStatus('speaking');
                        addSystemMessage('🔊 Playing audio response...');
                        playAudio(data.audio_url);
                    } else {
                        updateBotStatus('idle');
                    }
                } else {
                    // Display the assistant's response as a new message immediately
                    addBotMessage(data.response);
                    
                    // Add to conversation history
                    conversationHistory.push({
                        role: 'assistant',
                        content: data.response
                    });
                    
                    // Play audio response if available and in voice mode
                    if (mode === 'voice' && data.audio_url) {
                        updateBotStatus('speaking');
                        addSystemMessage('🔊 Playing audio response...');
                        playAudio(data.audio_url);
                    } else {
                        updateBotStatus('idle');
                    }
                }
                
                // Save session ID if provided
                if (data.session_id && !sessionId) {
                    sessionId = data.session_id;
                    console.log('Session ID set:', sessionId);
                }
            } else if (data.error) {
                // Remove the typing indicator
                removeTypingIndicator();
                
                console.error('Response error:', data.error);
                addBotMessage("I'm sorry, I encountered an issue while processing your request. Could you try again?");
                
                // Add to history
                conversationHistory.push({
                    role: 'assistant',
                    content: "I'm sorry, I encountered an issue while processing your request. Could you try again?"
                });
                
                updateBotStatus('error');
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
            removeTypingIndicator();
        }
    }

    // Send message via WebSocket
    function sendWebSocketMessage(text, audioBlob = null) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }
        
        try {
            // Show typing indicator immediately when sending a message
            addTypingIndicator();
            
            // Update bot status
            updateBotStatus('thinking');
            
            // Add to conversation history
            conversationHistory.push({
                role: 'user',
                content: text
            });
            
            // Create the message payload
            const payload = {
                text: text,
                history: conversationHistory.slice(0, -1) // Don't include the message we just added
            };
            
            // Add session ID if we have one
            if (sessionId) {
                payload.session_id = sessionId;
            }
            
            // Send the message
            ws.send(JSON.stringify(payload));
            return true;
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
            return false;
        }
    }
    
    // Add typing indicator as a separate message
    function addTypingIndicator() {
        // Remove any existing typing indicator
        removeTypingIndicator();
        
        // Create a new typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-message';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingMessages = document.querySelectorAll('.typing-message');
        typingMessages.forEach(msg => msg.remove());
    }

    // Switch to voice mode
    function switchToVoiceMode() {
        mode = 'voice';
        voiceModeBtn.classList.add('active');
        textModeBtn.classList.remove('active');
        voiceInput.classList.remove('hidden');
        textInput.classList.add('hidden');
        addSystemMessage('Switched to voice mode');
    }

    // Switch to text mode
    function switchToTextMode() {
        mode = 'text';
        textModeBtn.classList.add('active');
        voiceModeBtn.classList.remove('active');
        textInput.classList.remove('hidden');
        voiceInput.classList.add('hidden');
        addSystemMessage('Switched to text mode');
    }

    // Toggle recording state
    async function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            try {
                await startRecording();
            } catch (error) {
                console.error('Error starting recording:', error);
                showError('Could not access your microphone. Please check your permissions and try again.');
                switchToTextMode();
            }
        }
    }

    // Start recording audio
    async function startRecording() {
        try {
            audioChunks = [];
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await processAudio(audioBlob);
                
                // Release microphone
                stream.getTracks().forEach(track => track.stop());
            });

            // Start recording
            mediaRecorder.start();
            isRecording = true;
            micBtn.classList.add('recording');
            voiceStatusText.textContent = 'Listening... (Click again to stop)';
            voiceWaves.classList.add('active');
            
            // Automatically stop recording after 10 seconds
            setTimeout(() => {
                if (isRecording) {
                    stopRecording();
                }
            }, 10000);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            throw error;
        }
    }

    // Stop recording audio
    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            micBtn.classList.remove('recording');
            voiceStatusText.textContent = 'Processing...';
        }
    }

    // Process recorded audio
    async function processAudio(audioBlob) {
        try {
            updateBotStatus('thinking');
            
            // Create form data for the audio
            const formData = new FormData();
            formData.append('audio', audioBlob);
            formData.append('history', JSON.stringify(conversationHistory));
            
            // Send the audio to the server for processing
            const response = await fetch(`${API_ENDPOINT}/speech`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Process the response
            if (data.text) {
                // Display user's transcribed text
                addUserMessage(data.text);
                
                // Add to conversation history
                conversationHistory.push({
                    role: 'user',
                    content: data.text
                });
                
                // Send the transcribed text to the WebSocket
                if (isConnected) {
                    // Don't add user message again, just send to WebSocket
                    const payload = {
                        text: data.text,
                        history: conversationHistory.slice(0, -1) // Don't include the message we just added
                    };
                    
                    // Add session ID if we have one
                    if (sessionId) {
                        payload.session_id = sessionId;
                    }
                    
                    // Show typing indicator
                    addTypingIndicator();
                    
                    // Send the message
                    ws.send(JSON.stringify(payload));
                } else {
                    // If WebSocket is not connected, handle the response from the REST API
                    if (data.response) {
                        // Display the assistant's response
                        addBotMessage(data.response);
                        
                        // Add to conversation history
                        conversationHistory.push({
                            role: 'assistant',
                            content: data.response
                        });
                        
                        // Play audio response if available
                        if (data.audio_url) {
                            updateBotStatus('speaking');
                            playAudio(data.audio_url);
                        } else {
                            updateBotStatus('idle');
                        }
                    } else {
                        updateBotStatus('idle');
                    }
                }
            } else if (data.error) {
                showError(data.error);
                updateBotStatus('error');
            }

            // Reset UI
            voiceStatusText.textContent = 'Click the microphone to speak';
            voiceWaves.classList.remove('active');
            
        } catch (error) {
            console.error('Error processing audio:', error);
            showError("There was a problem processing your voice input. Please try again.");
            updateBotStatus('error');
            
            // Reset UI
            voiceStatusText.textContent = 'Click the microphone to speak';
            voiceWaves.classList.remove('active');
        }
    }

    // Send text message
    async function sendTextMessage() {
        const text = userInput.value.trim();
        
        if (!text) {
            return;
        }
        
        // Clear the input field
        userInput.value = '';
        
        // Add user message to chat
        addUserMessage(text);
        
        try {
            updateBotStatus('thinking');
            
            // Try to send via WebSocket first
            if (isConnected && sendWebSocketMessage(text)) {
                // Message sent successfully via WebSocket
                console.log('Message sent via WebSocket');
            } else {
                // Fall back to REST API if WebSocket is not available
                console.log('Falling back to REST API');
                
                let data;
                
                try {
                    // First try the regular endpoint
                    const response = await fetch(`${API_ENDPOINT}/text`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            text,
                            history: conversationHistory
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`Server error: ${response.status}`);
                    }

                    data = await response.json();
                }
                catch (apiError) {
                    console.error('Error with primary API, trying demo endpoint:', apiError);
                    
                    // If the main API fails, try the demo endpoint
                    try {
                        const demoResponse = await fetch(`${API_ENDPOINT}/demo/text`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                text,
                                history: conversationHistory
                            })
                        });
                        
                        if (!demoResponse.ok) {
                            throw new Error(`Demo server error: ${demoResponse.status}`);
                        }
                        
                        data = await demoResponse.json();
                    }
                    catch (demoError) {
                        console.error('Both API endpoints failed:', demoError);
                        showError("I couldn't connect to the server. Please check your internet connection and try again.");
                        return;
                    }
                }
                
                // Process the response from REST API
                if (data.response) {
                    // Display the assistant's response
                    addBotMessage(data.response);
                    
                    // Add to conversation history
                    conversationHistory.push({
                        role: 'assistant',
                        content: data.response
                    });
                    
                    // Play audio response if available and in voice mode
                    if (mode === 'voice') {
                        if (data.audio_url) {
                            updateBotStatus('speaking');
                            addSystemMessage('🔊 Playing audio response...');
                            playAudio(data.audio_url);
                        } else if (data.tts_status === 'unavailable' && !ttsWarningShown) {
                            // Show TTS warning only once per session
                            addSystemMessage('Text-to-speech is currently unavailable due to missing API keys.');
                            ttsWarningShown = true;
                            updateBotStatus('idle');
                        } else {
                            updateBotStatus('idle');
                        }
                    } else {
                        updateBotStatus('idle');
                    }
                } else if (data.error) {
                    console.error('Response error:', data.error);
                    addBotMessage("I'm sorry, I encountered an issue while processing your request. Could you try again?");
                    
                    // Add to history
                    conversationHistory.push({
                        role: 'assistant',
                        content: "I'm sorry, I encountered an issue while processing your request. Could you try again?"
                    });
                    
                    updateBotStatus('error');
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            showError("There was a problem sending your message. Please try again.");
            updateBotStatus('error');
        }
    }

    // Handle key press events (send message on Enter)
    function handleKeyPress(e) {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    }

    // Add user message to chat
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Add bot message to chat
    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${formatBotResponse(text)}</p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Format bot response (handle newlines)
    function formatBotResponse(text) {
        return escapeHtml(text).replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
    }

    // Escape HTML to prevent XSS
    function escapeHtml(unsafeText) {
        return unsafeText
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Add system message to chat (smaller, centered)
    function addSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `
            <div class="message-content system">
                <p><em>${escapeHtml(text)}</em></p>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Play audio from URL
    function playAudio(url) {
        try {
            // If URL is null, don't try to play audio
            if (!url) {
                console.log('No audio URL provided');
                updateBotStatus('idle');
                return;
            }
            
            console.log('Playing audio from URL:', url);
            
            // Make sure URL starts with / if it's a relative path
            if (!url.startsWith('http') && !url.startsWith('/')) {
                url = '/' + url;
            }
            
            // Create a visible audio player with controls
            const audioContainer = document.createElement('div');
            audioContainer.className = 'audio-player';
            audioContainer.style.margin = '10px 0';
            
            const audioElement = document.createElement('audio');
            audioElement.controls = true; // Show controls to allow user interaction
            audioElement.style.width = '100%';
            audioElement.src = url;
            
            // Add a play button for explicit user interaction
            const playButton = document.createElement('button');
            playButton.textContent = '▶️ Play Response';
            playButton.className = 'play-audio-btn';
            playButton.style.padding = '5px 10px';
            playButton.style.marginBottom = '5px';
            playButton.style.backgroundColor = '#4CAF50';
            playButton.style.color = 'white';
            playButton.style.border = 'none';
            playButton.style.borderRadius = '4px';
            playButton.style.cursor = 'pointer';
            
            // Add event listeners
            playButton.onclick = () => {
                audioElement.play()
                    .then(() => {
                        playButton.style.display = 'none';
                        audioElement.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error playing audio after click:', error);
                        addSystemMessage('Audio playback failed. Please try again or check browser settings.');
                    });
            };
            
            audioElement.onended = () => {
                console.log('Audio playback ended');
                updateBotStatus('idle');
                // Remove the audio player after playback
                setTimeout(() => {
                    if (audioContainer.parentNode) {
                        audioContainer.parentNode.removeChild(audioContainer);
                    }
                }, 2000);
            };
            
            audioElement.onerror = (e) => {
                console.error('Error playing audio:', e);
                addSystemMessage('Audio playback failed. Please check your browser settings.');
                updateBotStatus('idle');
            };
            
            // Add elements to the container
            audioContainer.appendChild(playButton);
            audioContainer.appendChild(audioElement);
            
            // Initially hide the audio element until play is clicked
            audioElement.style.display = 'none';
            
            // Add the audio container to the chat as a system message
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message system';
            messageDiv.appendChild(audioContainer);
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
            
            // Try auto-playing first (might work if user has interacted with page)
            audioElement.play()
                .then(() => {
                    // If autoplay works, hide the play button
                    playButton.style.display = 'none';
                    audioElement.style.display = 'block';
                    console.log('Audio autoplay successful');
                })
                .catch(error => {
                    // If autoplay fails, keep the play button visible for user interaction
                    console.log('Autoplay prevented, waiting for user interaction:', error);
                    // Keep the play button visible
                });
                
        } catch (error) {
            console.error('Error setting up audio playback:', error);
            addSystemMessage('Audio playback failed. Please try again.');
            updateBotStatus('idle');
        }
    }

    // Show error modal
    function showError(message) {
        // Add a helpful message about missing API keys if appropriate
        if (message && (message.includes("transcribe") || message.includes("audio"))) {
            message = "Voice recognition is currently unavailable due to missing API keys. Please use text input mode instead.";
        }
        
        errorMessage.textContent = message || 'An unknown error occurred.';
        errorModal.classList.add('show');
        
        // Automatically switch to text mode if there's a voice-related error
        if (mode === 'voice') {
            setTimeout(() => {
                switchToTextMode();
            }, 1000);
        }
    }

    // Close error modal
    function closeErrorModal() {
        errorModal.classList.remove('show');
    }

    // Update bot status indicator
    function updateBotStatus(status) {
        switch (status) {
            case 'idle':
                botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Idle</span>';
                botStatus.className = 'idle';
                break;
            case 'thinking':
                botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Thinking</span>';
                botStatus.className = 'thinking';
                break;
            case 'generating':
                botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Generating</span>';
                botStatus.className = 'generating';
                break;
            case 'speaking':
                botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Speaking</span>';
                botStatus.className = 'speaking';
                break;
            case 'error':
                botStatus.innerHTML = '<i class="fas fa-circle"></i><span>Error</span>';
                botStatus.className = 'error';
                break;
        }
    }

    // Update connection status indicator
    function updateConnectionStatus(status) {
        switch (status) {
            case 'connected':
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
                connectionStatus.className = 'connected';
                break;
            case 'connecting':
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Connecting...</span>';
                connectionStatus.className = 'connecting';
                break;
            case 'disconnected':
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
                connectionStatus.className = 'disconnected';
                break;
            case 'error':
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Connection Error</span>';
                connectionStatus.className = 'error';
                break;
        }
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Initialize the application
    let connectionStatusShown = false;
    let ttsWarningShown = false;
    init();
}); 