import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileAudio,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export default function UploadRecording({ onUploadComplete, onSelectMeeting }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [meetingId, setMeetingId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [error, setError] = useState(null);

  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const supportedFormats = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.webm', '.mp4'];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!supportedFormats.includes(ext)) {
      setError(`Unsupported format '${ext}'. Allowed: ${supportedFormats.join(', ')}`);
      return;
    }
    setError(null);
    setSelectedFile(file);
    if (!title) {
      const cleanTitle = file.name
        .substring(0, file.name.lastIndexOf('.'))
        .replace(/[-_]/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
      setTitle(cleanTitle);
    }
  };

  const startUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError(null);
      setStatusData({ progress: 10, current_step: 'Uploading recording to server...' });

      const res = await api.uploadRecording(selectedFile, title, true);
      setMeetingId(res.id);

      // Start polling status
      pollStatus(res.id);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Upload failed');
      setUploading(false);
    }
  };

  const pollStatus = (id) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const s = await api.getProcessingStatus(id);
        setStatusData(s);

        if (s.status === 'completed') {
          clearInterval(pollIntervalRef.current);
          setUploading(false);
          if (onUploadComplete) onUploadComplete(id);
        } else if (s.status === 'failed') {
          clearInterval(pollIntervalRef.current);
          setUploading(false);
          setError(s.error_message || 'Processing pipeline encountered an error.');
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 2000);
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const resetForm = () => {
    setSelectedFile(null);
    setTitle('');
    setUploading(false);
    setMeetingId(null);
    setStatusData(null);
    setError(null);
  };

  const isCompleted = statusData?.status === 'completed';

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      {/* Upload Header Info */}
      <div style={{ marginBottom: 24, textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
          Upload Meeting Recording
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          EchoNote automatically generates timestamped transcripts, extracts evidence-backed decisions, and catalogs action items.
        </p>
      </div>

      {error && (
        <div
          className="card"
          style={{
            padding: 16,
            marginBottom: 20,
            borderColor: 'var(--danger-border)',
            backgroundColor: 'var(--danger-bg)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{error}</span>
          </div>
        </div>
      )}

      {/* Upload Card / Dropzone */}
      <div className="card" style={{ padding: 28 }}>
        {!selectedFile ? (
          <div>
            <div
              className={`dropzone ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={supportedFormats.join(',')}
                onChange={handleFileInput}
                style={{ display: 'none' }}
              />

              <div className="dropzone-icon">
                <UploadCloud size={28} />
              </div>

              <div>
                <p style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                  Drag and drop your audio file here, or browse
                </p>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  Supports long recordings (up to 250MB) with automatic chunk processing
                </p>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                {supportedFormats.map((fmt) => (
                  <span key={fmt} className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                    {fmt.toUpperCase().replace('.', '')}
                  </span>
                ))}
              </div>
            </div>

            <div
              style={{
                marginTop: 20,
                padding: 12,
                borderRadius: 'var(--radius-md)',
                backgroundColor: '#f8fafc',
                border: '1px solid var(--border-color)',
                display: 'flex',
                gap: 10,
                alignItems: 'flex-start',
                fontSize: '0.8rem',
                color: 'var(--text-muted)'
              }}
            >
              <Info size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <strong>Evidence-Backed Pipeline:</strong> Ingested audio is normalized via FFmpeg into standard 16kHz mono audio, processed through chunked Whisper speech recognition, and synthesized by the LLM with strict excerpt verification.
              </div>
            </div>
          </div>
        ) : (
          <div>
            {/* File info banner */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 16,
                borderRadius: 'var(--radius-md)',
                backgroundColor: '#f8fafc',
                border: '1px solid var(--border-color)',
                marginBottom: 20
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <FileAudio size={20} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                    {selectedFile.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </div>
                </div>
              </div>

              {!uploading && !isCompleted && (
                <button onClick={resetForm} className="btn btn-secondary btn-sm">
                  Change File
                </button>
              )}
            </div>

            {/* Title Input */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: 6 }}>
                Meeting Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploading || isCompleted}
                placeholder="e.g. Q3 Architecture Review & Roadmap"
                className="input"
              />
            </div>

            {/* Processing Progress Bar */}
            {uploading && statusData && (
              <div style={{ marginBottom: 24, padding: 16, backgroundColor: '#fafbfc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.875rem', fontWeight: 500 }}>
                    <Loader2 size={16} className="spin" color="var(--primary)" />
                    <span>{statusData.current_step || 'Processing meeting audio...'}</span>
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--primary)' }}>
                    {statusData.progress}%
                  </span>
                </div>

                <div className="progress-container">
                  <div className="progress-bar" style={{ width: `${statusData.progress}%` }} />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 8 }}>
                  <span>FFmpeg Normalize</span>
                  <span>Whisper Chunks</span>
                  <span>LLM Extraction</span>
                  <span>Evidence Validation</span>
                </div>
              </div>
            )}

            {/* Completed state */}
            {isCompleted && (
              <div
                style={{
                  padding: 24,
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--success-bg)',
                  border: '1px solid var(--success-border)',
                  textAlign: 'center',
                  marginBottom: 20
                }}
              >
                <CheckCircle2 size={36} color="var(--success)" style={{ margin: '0 auto 8px' }} />
                <h4 style={{ fontWeight: 700, color: 'var(--success)', marginBottom: 4 }}>
                  Meeting Ingested & Analyzed Successfully!
                </h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
                  Timestamped transcript, speaker labeling, decisions and evidence-backed action items are ready.
                </p>

                <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                  <button onClick={() => onSelectMeeting(meetingId)} className="btn btn-primary">
                    <span>View Meeting Intelligence</span>
                    <ArrowRight size={16} />
                  </button>
                  <button onClick={resetForm} className="btn btn-secondary">
                    <span>Upload Another</span>
                  </button>
                </div>
              </div>
            )}

            {/* Action buttons if not yet uploading */}
            {!uploading && !isCompleted && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button onClick={resetForm} className="btn btn-secondary">
                  Cancel
                </button>
                <button onClick={startUpload} className="btn btn-primary">
                  <UploadCloud size={16} />
                  <span>Start Processing</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
