/**
 * AudioPlayer Component - Plays audio responses
 */
const AudioPlayer = ({ audioUrl, audioStatus }) => {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [audioError, setAudioError] = React.useState(false);
  const [isAudioReady, setIsAudioReady] = React.useState(false);
  const [isPolling, setIsPolling] = React.useState(false);
  const audioRef = React.useRef(null);
  const pollingIntervalRef = React.useRef(null);
  
  // Ensure we have the correct audio URL (handle both .wav and .mp3)
  const getAudioUrl = () => {
    if (!audioUrl) return null;
    
    // If URL ends with .mp3 but the server is providing .wav files
    if (audioUrl.endsWith('.mp3')) {
      const baseUrl = audioUrl.substring(0, audioUrl.length - 4);
      return `${baseUrl}.wav`;
    }
    
    return audioUrl;
  };
  
  // Handle play/pause button click
  const togglePlay = () => {
    if (!audioRef.current || audioError || !isAudioReady) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      // Reset error state on new play attempt
      setAudioError(false);
      
      // Attempt to play and handle any errors
      const playPromise = audioRef.current.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            // Playback started successfully
          })
          .catch(error => {
            console.error('Error playing audio:', error);
            setIsPlaying(false);
            setAudioError(true);
          });
      }
    }
  };

  // Check if audio file exists by making a HEAD request
  const checkAudioExists = () => {
    if (!audioUrl) return;
    
    fetch(getAudioUrl(), { method: 'HEAD' })
      .then(response => {
        if (response.ok) {
          setIsAudioReady(true);
          setIsPolling(false);
          clearInterval(pollingIntervalRef.current);
        }
      })
      .catch(error => {
        console.log('Audio file not ready yet:', error);
      });
  };
  
  // Start polling for audio file when URL is available but status is "generating"
  React.useEffect(() => {
    if (audioUrl && audioStatus === "generating" && !isAudioReady && !isPolling) {
      setIsPolling(true);
      
      // Check immediately
      checkAudioExists();
      
      // Then set up polling
      pollingIntervalRef.current = setInterval(checkAudioExists, 1000);
    }
    
    // If we get a new audio URL and it's not generating, mark as ready
    if (audioUrl && audioStatus !== "generating") {
      setIsAudioReady(true);
    }
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [audioUrl, audioStatus, isAudioReady, isPolling]);
  
  // Update playing state when audio plays or pauses
  React.useEffect(() => {
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);
    const handleError = (e) => {
      console.error('Audio error:', e);
      setAudioError(true);
      setIsPlaying(false);
    };
    
    if (audioRef.current) {
      audioRef.current.addEventListener('play', handlePlay);
      audioRef.current.addEventListener('pause', handlePause);
      audioRef.current.addEventListener('ended', handleEnded);
      audioRef.current.addEventListener('error', handleError);
    }
    
    return () => {
      if (audioRef.current) {
        audioRef.current.removeEventListener('play', handlePlay);
        audioRef.current.removeEventListener('pause', handlePause);
        audioRef.current.removeEventListener('ended', handleEnded);
        audioRef.current.removeEventListener('error', handleError);
      }
    };
  }, []);
  
  // If there's an audio error, don't render the player
  if (audioError) {
    return (
      <div className="audio-player error">
        <span className="audio-error">
          <i className="fas fa-exclamation-circle"></i> Audio unavailable
        </span>
      </div>
    );
  }
  
  // If audio is still generating, show loading state
  if (!isAudioReady && audioUrl) {
    return (
      <div className="audio-player loading">
        <span className="audio-loading">
          <i className="fas fa-spinner fa-spin"></i> Generating audio...
        </span>
      </div>
    );
  }
  
  return (
    <div className="audio-player">
      <button 
        className="play-audio-btn"
        onClick={togglePlay}
        disabled={!isAudioReady}
      >
        <i className={`fas ${isPlaying ? 'fa-pause' : 'fa-play'}`}></i>
        {isPlaying ? ' Pause Audio' : ' Play Audio'}
      </button>
      <audio 
        ref={audioRef}
        src={getAudioUrl()} 
        preload="auto"
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
        onError={() => setAudioError(true)}
      />
    </div>
  );
}; 