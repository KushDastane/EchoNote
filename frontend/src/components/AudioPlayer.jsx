import React, { useRef, useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX
} from 'lucide-react';

function formatTime(seconds) {
  if (!seconds || isNaN(seconds) || seconds < 0) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const hrs = Math.floor(mins / 60);
  if (hrs > 0) {
    const remMins = mins % 60;
    return `${hrs.toString().padStart(2, '0')}:${remMins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function AudioPlayer({ audioUrl, seekTimestamp, onTimeUpdate }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  // Handle external seek requests (e.g. clicking evidence excerpt or transcript timestamp)
  useEffect(() => {
    if (seekTimestamp !== null && seekTimestamp !== undefined && audioRef.current) {
      audioRef.current.currentTime = seekTimestamp;
      setCurrentTime(seekTimestamp);
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [seekTimestamp]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleSeek = (e) => {
    const target = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = target;
      setCurrentTime(target);
    }
  };

  const skip = (delta) => {
    if (!audioRef.current) return;
    const newTime = Math.max(0, Math.min(duration, audioRef.current.currentTime + delta));
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const changeRate = (rate) => {
    setPlaybackRate(rate);
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  return (
    <div className="audio-player-bar">
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
        onLoadedMetadata={() => setDuration(audioRef.current ? audioRef.current.duration : 0)}
        onTimeUpdate={() => {
          if (audioRef.current) {
            const cur = audioRef.current.currentTime;
            setCurrentTime(cur);
            if (onTimeUpdate) onTimeUpdate(cur);
          }
        }}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="audio-controls">
        <button
          onClick={() => skip(-10)}
          className="audio-btn"
          title="Rewind 10 seconds"
        >
          <RotateCcw size={16} />
        </button>

        <button
          onClick={togglePlay}
          className="audio-btn primary"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
        </button>

        <button
          onClick={() => skip(10)}
          className="audio-btn"
          title="Forward 10 seconds"
        >
          <RotateCw size={16} />
        </button>
      </div>

      <div className="audio-timeline">
        <span className="timestamp-text">{formatTime(currentTime)}</span>
        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          className="timeline-slider"
        />
        <span className="timestamp-text">{formatTime(duration)}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={toggleMute}
          className="audio-btn"
          title={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>

        <div style={{ display: 'flex', gap: 4 }}>
          {[1, 1.25, 1.5].map((rate) => (
            <button
              key={rate}
              onClick={() => changeRate(rate)}
              className="btn btn-secondary btn-sm"
              style={{
                padding: '4px 8px',
                fontSize: '0.7rem',
                backgroundColor: playbackRate === rate ? 'var(--primary-light)' : 'transparent',
                color: playbackRate === rate ? 'var(--primary)' : 'var(--text-muted)',
                borderColor: playbackRate === rate ? 'var(--primary-border)' : 'var(--border-color)',
                fontWeight: playbackRate === rate ? 600 : 400
              }}
            >
              {rate}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
