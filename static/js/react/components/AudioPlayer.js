/**
 * AudioPlayer Component - Plays audio responses
 */
const AudioPlayer = ({ audioUrl }) => {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const audioRef = React.useRef(null);
  
  // Handle play/pause button click
  const togglePlay = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
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
          });
      }
    }
  };
  
  // Update playing state when audio plays or pauses
  React.useEffect(() => {
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);
    
    if (audioRef.current) {
      audioRef.current.addEventListener('play', handlePlay);
      audioRef.current.addEventListener('pause', handlePause);
      audioRef.current.addEventListener('ended', handleEnded);
    }
    
    return () => {
      if (audioRef.current) {
        audioRef.current.removeEventListener('play', handlePlay);
        audioRef.current.removeEventListener('pause', handlePause);
        audioRef.current.removeEventListener('ended', handleEnded);
      }
    };
  }, []);
  
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
        src={audioUrl} 
        preload="auto"
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />
    </div>
  );
}; 