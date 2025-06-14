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

    // State
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let mode = 'voice';
    let conversationHistory = [];
    let isConnected = false;

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
            
            // Create form data for the audio file
            const formData = new FormData();
            formData.append('audio', audioBlob);
            
            // Add conversation history
            formData.append('history', JSON.stringify(conversationHistory));
            
            let data;
            
            try {
                // First try the regular endpoint
                const response = await fetch(`${API_ENDPOINT}/speech`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }

                data = await response.json();
            } catch (apiError) {
                console.warn('Regular API error, falling back to demo endpoint:', apiError);
                
                // If that fails, use the demo endpoint
                const demoResponse = await fetch(`${API_ENDPOINT}/demo/speech`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!demoResponse.ok) {
                    throw new Error(`Demo API error: ${demoResponse.status}`);
                }
                
                data = await demoResponse.json();
            }
            
            // Process the response
            if (data.text) {
                // Display user's transcribed text
                addUserMessage(data.text);
                
                // Add to conversation history
                conversationHistory.push({
                    role: 'user',
                    content: data.text
                });
                
                // If there's a response from the assistant
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
            } else if (data.error) {
                showError(data.error);
                updateBotStatus('error');
            }

            // Reset UI
            voiceStatusText.textContent = 'Click the microphone to speak';
            voiceWaves.classList.remove('active');
            
        } catch (error) {
            console.error('Error processing audio:', error);
            
            // Show a helpful error message
            showError("Voice recognition is currently unavailable due to missing API keys. Please use text input mode instead.");
            
            // Switch to text mode automatically
            setTimeout(() => {
                switchToTextMode();
            }, 1000);
            
            voiceStatusText.textContent = 'Click the microphone to speak';
            voiceWaves.classList.remove('active');
            updateBotStatus('idle');
        }
    }

    // Handle sending text messages
    async function sendTextMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Clear input
        userInput.value = '';
        
        // Display user message
        addUserMessage(text);
        
        // Add to conversation history
        conversationHistory.push({
            role: 'user',
            content: text
        });

        try {
            updateBotStatus('thinking');
            
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
            } catch (apiError) {
                console.warn('Regular API error, falling back to demo endpoint:', apiError);
                
                // If that fails, use the demo endpoint
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
                    throw new Error(`Demo API error: ${demoResponse.status}`);
                }
                
                data = await demoResponse.json();
            }
            
            // Process the response
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
            
        } catch (error) {
            console.error('Error sending text message:', error);
            addBotMessage("I'm sorry, I'm experiencing technical difficulties. Please try again later.");
            
            // Add to history
            conversationHistory.push({
                role: 'assistant',
                content: "I'm sorry, I'm experiencing technical difficulties. Please try again later."
            });
            
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

    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Check server connection
    async function checkConnection() {
        try {
            const response = await fetch(`${API_ENDPOINT}/health`);
            if (response.ok) {
                const data = await response.json();
                isConnected = true;
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Connected</span>';
                connectionStatus.className = 'connected';
                
                // Show limited functionality message if needed
                if (data.status === 'limited' && !connectionStatusShown) {
                    connectionStatusShown = true;
                    addSystemMessage('⚠️ Running with limited functionality. Some features may not work as expected.');
                }
            } else {
                isConnected = false;
                connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
                connectionStatus.className = 'disconnected';
            }
        } catch (error) {
            isConnected = false;
            connectionStatus.innerHTML = '<i class="fas fa-circle"></i><span>Disconnected</span>';
            connectionStatus.className = 'disconnected';
        }
    }

    // Initialize the application
    let connectionStatusShown = false;
    let ttsWarningShown = false;
    init();
    
    // Check connection every 30 seconds
    checkConnection();
    setInterval(checkConnection, 30000);
}); 