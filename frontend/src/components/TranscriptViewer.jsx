import React, { useState, useEffect, useRef } from 'react';
import { Search, Volume2 } from 'lucide-react';

function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function TranscriptViewer({
  segments = [],
  currentTime = 0,
  targetTimestamp = null,
  onSeek
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const segmentRefs = useRef({});

  // Auto-scroll to target segment when jumped from evidence reference
  useEffect(() => {
    if (targetTimestamp !== null && targetTimestamp !== undefined && segments.length > 0) {
      // Find segment matching or closest to targetTimestamp
      let targetSeg = segments.find(
        (s) => Math.abs(s.start_time - targetTimestamp) < 3.0 || (targetTimestamp >= s.start_time && targetTimestamp <= s.end_time)
      );
      if (!targetSeg && segments.length > 0) {
        // closest
        targetSeg = segments.reduce((prev, curr) =>
          Math.abs(curr.start_time - targetTimestamp) < Math.abs(prev.start_time - targetTimestamp) ? curr : prev
        );
      }

      if (targetSeg && segmentRefs.current[targetSeg.id]) {
        segmentRefs.current[targetSeg.id].scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }
  }, [targetTimestamp, segments]);

  const filtered = segments.filter((s) =>
    s.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.speaker.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3 className="card-title">Meeting Transcript</h3>
          <span className="badge badge-neutral">{segments.length} segments</span>
        </div>

        <div style={{ position: 'relative', width: 220 }}>
          <Search
            size={14}
            style={{
              position: 'absolute',
              left: 10,
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-light)'
            }}
          />
          <input
            type="text"
            placeholder="Filter transcript..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input"
            style={{ paddingLeft: 30, fontSize: '0.8rem', height: 32 }}
          />
        </div>
      </div>

      <div className="card-body">
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)' }}>
            No transcript segments match your filter.
          </div>
        ) : (
          <div className="transcript-box">
            {filtered.map((seg) => {
              const isPlaying = currentTime >= seg.start_time && currentTime <= seg.end_time;
              const isEvidenceTarget =
                targetTimestamp !== null &&
                (Math.abs(seg.start_time - targetTimestamp) < 2.0 ||
                  (targetTimestamp >= seg.start_time && targetTimestamp <= seg.end_time));

              return (
                <div
                  key={seg.id}
                  ref={(el) => (segmentRefs.current[seg.id] = el)}
                  onClick={() => onSeek(seg.start_time)}
                  className={`transcript-segment ${isPlaying ? 'active-playing' : ''} ${
                    isEvidenceTarget ? 'evidence-target' : ''
                  }`}
                >
                  <div className="segment-meta">
                    <span className="segment-speaker">{seg.speaker}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {isPlaying && <Volume2 size={12} color="var(--primary)" />}
                      <span className="segment-time">
                        {formatTime(seg.start_time)} - {formatTime(seg.end_time)}
                      </span>
                    </div>
                  </div>
                  <p className="segment-text">{seg.text}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
