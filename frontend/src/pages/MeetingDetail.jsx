import React, { useEffect, useState } from 'react';
import {
  ArrowLeft,
  FileAudio,
  Calendar,
  Clock,
  RefreshCw,
  AlertCircle,
  FileText,
  Lightbulb,
  CheckSquare,
  MessageSquare,
  SlidersHorizontal
} from 'lucide-react';
import { api } from '../services/api';
import AudioPlayer from '../components/AudioPlayer';
import TranscriptViewer from '../components/TranscriptViewer';
import InsightsPanel from '../components/InsightsPanel';
import DecisionsList from '../components/DecisionsList';
import ActionItemsList from '../components/ActionItemsList';

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hrs > 0) {
    return `${hrs}h ${mins}m ${secs}s`;
  }
  return `${mins}m ${secs}s`;
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

export default function MeetingDetail({ meetingId, onBack }) {
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' or 'transcript'

  // Audio synchronization state
  const [currentTime, setCurrentTime] = useState(0);
  const [seekTimestamp, setSeekTimestamp] = useState(null);
  const [targetEvidenceTimestamp, setTargetEvidenceTimestamp] = useState(null);

  const fetchMeeting = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMeeting(meetingId);
      setMeeting(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to load meeting details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeeting();
  }, [meetingId]);

  // Jump from evidence excerpt or transcript timestamp
  const handleJumpToEvidence = (timestamp, evidenceText) => {
    if (timestamp !== null && timestamp !== undefined) {
      setSeekTimestamp(timestamp);
      setTargetEvidenceTimestamp(timestamp);
      // If user is on mobile/tabs, switch to transcript view if desired or keep side-by-side
    }
  };

  const handleActionToggle = async (actionId, newStatus) => {
    try {
      // Optimistic update
      setMeeting((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          action_items: prev.action_items.map((a) =>
            a.id === actionId ? { ...a, status: newStatus } : a
          )
        };
      });

      await api.updateActionItem(meetingId, actionId, { status: newStatus });
    } catch (err) {
      console.error(err);
      fetchMeeting(); // rollback on failure
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--text-muted)' }}>
        Loading meeting intelligence...
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="card" style={{ padding: 24, borderColor: 'var(--danger-border)', backgroundColor: 'var(--danger-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)', marginBottom: 12 }}>
          <AlertCircle size={20} />
          <strong>{error || 'Meeting not found'}</strong>
        </div>
        <button onClick={onBack} className="btn btn-secondary btn-sm">
          <ArrowLeft size={14} />
          <span>Back to Meetings</span>
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Top Navigation & Meeting Header */}
      <div style={{ marginBottom: 20 }}>
        <button
          onClick={onBack}
          className="btn btn-secondary btn-sm"
          style={{ marginBottom: 16 }}
        >
          <ArrowLeft size={14} />
          <span>Back to Meetings</span>
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontSize: '1.625rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
              {meeting.title}
            </h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '0.8125rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Calendar size={14} />
                {formatDate(meeting.created_at)}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Clock size={14} />
                {formatDuration(meeting.duration)}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <FileAudio size={14} />
                {meeting.original_filename}
              </span>
              <span
                className={`badge ${
                  meeting.status === 'completed'
                    ? 'badge-verified'
                    : meeting.status === 'processing'
                    ? 'badge-primary'
                    : 'badge-neutral'
                }`}
              >
                {meeting.status}
              </span>
            </div>
          </div>

          <button onClick={fetchMeeting} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Synchronized Audio Player */}
      <AudioPlayer
        audioUrl={api.getAudioUrl(meeting.id)}
        seekTimestamp={seekTimestamp}
        onTimeUpdate={(time) => setCurrentTime(time)}
      />

      {/* Main Content Layout: Two-Column Responsive Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 24, alignItems: 'start' }}>
        {/* Left Column: Evidence-Backed Intelligence */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Executive Summary & Insights */}
          <InsightsPanel
            summary={meeting.summary}
            keyPoints={meeting.key_points}
            unresolvedQuestions={meeting.unresolved_questions}
            topics={meeting.important_topics}
          />

          {/* Agreed Decisions with Evidence */}
          <DecisionsList
            decisions={meeting.decisions}
            onJumpToEvidence={handleJumpToEvidence}
          />

          {/* Action Items with Verification & Owner Tracking */}
          <ActionItemsList
            actionItems={meeting.action_items}
            onToggleStatus={handleActionToggle}
            onJumpToEvidence={handleJumpToEvidence}
          />
        </div>

        {/* Right Column: Interactive Timestamped Transcript */}
        <div>
          <TranscriptViewer
            segments={meeting.segments}
            currentTime={currentTime}
            targetTimestamp={targetEvidenceTimestamp}
            onSeek={(ts) => {
              setSeekTimestamp(ts);
              setTargetEvidenceTimestamp(ts);
            }}
          />
        </div>
      </div>
    </div>
  );
}
