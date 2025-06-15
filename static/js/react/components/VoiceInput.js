/**
 * VoiceInput Component - Handles voice recording and status display
 */
const VoiceInput = ({ onSendVoice, isRecording, setIsRecording, botStatus }) => {
  const [audioBlob, setAudioBlob] = React.useState(null);
  const [recordingTime, setRecordingTime] = React.useState(0);
  const [errorMessage, setErrorMessage] = React.useState('');
  const mediaRecorderRef = React.useRef(null);
  const audioChunksRef = React.useRef([]);
  const timerRef = React.useRef(null);
  const audioContextRef = React.useRef(null);
  
  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      stopRecording();
    };
  }, []);
  
  // Update recording timer and show warning at 15 seconds
  React.useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          // Show warning when approaching max recording time
          if (newTime === 15) {
            setErrorMessage('Recording will end in 5 seconds...');
          }
          return newTime;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setRecordingTime(0);
      setErrorMessage('');
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);
  
  // Format recording time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
  
  // Start recording audio
  const startRecording = async () => {
    try {
      setErrorMessage('');
      // Request audio at 16kHz if possible for better compatibility with ElevenLabs
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      // Reset audio chunks
      audioChunksRef.current = [];
      
      // Create media recorder - use WAV format (audio/wav) for better compatibility
      const options = { mimeType: 'audio/webm' };
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      
      // Handle data available event
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // Handle recording stop event
      mediaRecorder.onstop = () => {
        // Create blob from audio chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        
        // Send the audio blob
        onSendVoice(audioBlob);
        
        // Stop all audio tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording
      mediaRecorder.start(100); // Collect data in 100ms chunks for smoother stop
      setIsRecording(true);
      
      // Auto-stop after 20 seconds
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          stopRecording();
        }
      }, 20000);
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setErrorMessage('Could not access microphone. Please check your browser permissions.');
    }
  };
  
  // Stop recording audio
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  // Toggle recording state
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };
  
  // Determine if the mic button should be disabled
  const isMicDisabled = botStatus === 'thinking' || botStatus === 'speaking';
  
  // Get the appropriate status text
  const getStatusText = () => {
    if (errorMessage) {
      return errorMessage;
    }
    
    if (isRecording) {
      return `Recording... ${formatTime(recordingTime)}`;
    }
    
    switch (botStatus) {
      case 'thinking':
        return 'Processing your voice...';
      case 'speaking':
        return 'Speaking...';
      default:
        return 'Click to speak';
    }
  };
  
  return (
    <div className="voice-input">
      <button 
        className={`mic-btn ${isRecording ? 'recording' : ''} ${errorMessage ? 'error' : ''}`} 
        onClick={toggleRecording}
        disabled={isMicDisabled}
      >
        <i className={`fas ${isRecording ? 'fa-stop' : 'fa-microphone'}`}></i>
      </button>
      
      <div className="voice-status">
        <div id="voice-status-text" className={errorMessage ? 'error' : ''}>{getStatusText()}</div>
        <div className={`voice-waves ${isRecording ? 'active' : ''}`}>
          <span></span>
          <span></span>
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}; 