/**
 * AudioPlayer Component - Plays audio responses
 */
const AudioPlayer = ({ audioUrl }) => {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [audioError, setAudioError] = React.useState(false);
  const audioRef = React.useRef(null);
  
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
    if (!audioRef.current || audioError) return;
    
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
  
  return (
    <div className="audio-player">
      <button 
        className="play-audio-btn"
        onClick={togglePlay}
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