// app.js

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const voiceInput = document.getElementById('voice-input');
const textInput = document.getElementById('text-input');
const voiceModeBtn = document.getElementById('voice-mode-btn');
const textModeBtn = document.getElementById('text-mode-btn');
const botStatus = document.getElementById('bot-status');
const waitingAnimation = document.getElementById('waiting-animation');
const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');
const closeErrorBtn = document.getElementById('close-error-btn');

let conversationHistory = [];
let lastRequestTimestamp = null;

// --- Micro-animations for buttons ---
[micBtn, sendBtn].forEach(btn => {
    btn.addEventListener('mousedown', () => btn.style.transform = 'scale(0.96)');
    btn.addEventListener('mouseup', () => btn.style.transform = '');
    btn.addEventListener('mouseleave', () => btn.style.transform = '');
});

// --- Mode toggle ---
voiceModeBtn.addEventListener('click', () => {
    voiceModeBtn.classList.add('active');
    textModeBtn.classList.remove('active');
    voiceInput.classList.remove('hidden');
    textInput.classList.add('hidden');
});
textModeBtn.addEventListener('click', () => {
    textModeBtn.classList.add('active');
    voiceModeBtn.classList.remove('active');
    voiceInput.classList.add('hidden');
    textInput.classList.remove('hidden');
});

// --- Error Modal ---
closeErrorBtn.addEventListener('click', () => {
    errorModal.classList.remove('show');
});

// --- Utility Functions ---
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateBotStatus(status) {
    const icon = botStatus.querySelector('i');
    const span = botStatus.querySelector('span');
    botStatus.className = `bot-status ${status}`;
    switch (status) {
        case 'thinking':
            icon.style.color = 'var(--primary-color)';
            span.textContent = 'Thinking...';
            break;
        case 'speaking':
            icon.style.color = 'var(--success-color)';
            span.textContent = 'Speaking';
            break;
        case 'error':
            icon.style.color = 'var(--error-color)';
            span.textContent = 'Error';
            break;
        default:
            icon.style.color = 'var(--accent-color)';
            span.textContent = 'Idle';
    }
}

function showWaitingAnimation() {
    waitingAnimation.style.display = 'flex';
}
function hideWaitingAnimation() {
    waitingAnimation.style.display = 'none';
}

// --- Message Rendering ---
function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHTML(text)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text, elapsedMs = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    let responseTimeHtml = '';
    if (elapsedMs !== null) {
        const seconds = (elapsedMs / 1000).toFixed(2);
        responseTimeHtml = `<span class="response-time">⏱ ${seconds}s</span>`;
    }
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHTML(text)}${responseTimeHtml}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHTML(text)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function escapeHTML(str) {
    return str.replace(/[&<>"']/g, function(m) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[m];
    });
}

// --- Sending Text Message ---
sendBtn.addEventListener('click', sendTextMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendTextMessage();
});

async function sendTextMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = '';
    addUserMessage(text);
    conversationHistory.push({ role: 'user', content: text });

    updateBotStatus('thinking');
    showWaitingAnimation();
    lastRequestTimestamp = performance.now();

    try {
        // Replace this with your actual API call
        const response = await fetch('/api/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, history: conversationHistory })
        });
        const data = await response.json();

        if (data.response) {
            const elapsed = performance.now() - lastRequestTimestamp;
            addBotMessage(data.response, elapsed);
            conversationHistory.push({ role: 'assistant', content: data.response });
            updateBotStatus('idle');
        } else {
            throw new Error('No response from server.');
        }
    } catch (err) {
        updateBotStatus('error');
        addSystemMessage('An error occurred while getting the response.');
        errorMessage.textContent = err.message || 'Unknown error';
        errorModal.classList.add('show');
    } finally {
        hideWaitingAnimation();
    }
}

// --- Voice Input (Web Speech API Example) ---
let recognition = null;
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    micBtn.addEventListener('click', () => {
        recognition.start();
        micBtn.classList.add('recording');
        document.getElementById('voice-status-text').textContent = "Listening...";
        document.getElementById('voice-waves').classList.add('active');
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        micBtn.classList.remove('recording');
        document.getElementById('voice-status-text').textContent = "Click the microphone to speak";
        document.getElementById('voice-waves').classList.remove('active');
        if (transcript) processVoiceText(transcript);
    };

    recognition.onerror = (event) => {
        micBtn.classList.remove('recording');
        document.getElementById('voice-status-text').textContent = "Click the microphone to speak";
        document.getElementById('voice-waves').classList.remove('active');
        addSystemMessage('Voice recognition error.');
    };

    recognition.onend = () => {
        micBtn.classList.remove('recording');
        document.getElementById('voice-status-text').textContent = "Click the microphone to speak";
        document.getElementById('voice-waves').classList.remove('active');
    };
} else {
    micBtn.disabled = true;
    document.getElementById('voice-status-text').textContent = "Voice input not supported in this browser.";
}

async function processVoiceText(text) {
    addUserMessage(text);
    conversationHistory.push({ role: 'user', content: text });

    updateBotStatus('thinking');
    showWaitingAnimation();
    lastRequestTimestamp = performance.now();

    try {
        // Replace this with your actual API call
        const response = await fetch('/api/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, history: conversationHistory })
        });
        const data = await response.json();

        if (data.response) {
            const elapsed = performance.now() - lastRequestTimestamp;
            addBotMessage(data.response, elapsed);
            conversationHistory.push({ role: 'assistant', content: data.response });
            updateBotStatus('idle');
        } else {
            throw new Error('No response from server.');
        }
    } catch (err) {
        updateBotStatus('error');
        addSystemMessage('An error occurred while getting the response.');
        errorMessage.textContent = err.message || 'Unknown error';
        errorModal.classList.add('show');
    } finally {
        hideWaitingAnimation();
    }
}

// --- Initialization ---
window.addEventListener('DOMContentLoaded', () => {
    updateBotStatus('idle');
    hideWaitingAnimation();
});
