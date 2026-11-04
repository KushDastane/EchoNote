import React, { useEffect, useState } from 'react';
import {
  FileAudio,
  Clock,
  CheckSquare,
  AlertCircle,
  ShieldCheck,
  UploadCloud,
  ArrowRight
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { api } from '../services/api';

function formatDuration(seconds) {
  if (!seconds || isNaN(seconds)) return '0m';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function Overview({ onNavigate, onSelectMeeting }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
      setError('Unable to fetch dashboard metrics. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0', color: 'var(--text-muted)' }}>
        Loading dashboard metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ padding: 24, borderColor: 'var(--danger-border)', backgroundColor: 'var(--danger-bg)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)' }}>
          <AlertCircle size={20} />
          <strong>{error}</strong>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Metrics Row */}
      <div className="metrics-grid">
        <MetricCard
          title="Total Meetings"
          value={metrics?.total_meetings || 0}
          subtext="Processed recordings"
          icon={FileAudio}
          color="var(--primary)"
        />
        <MetricCard
          title="Total Duration"
          value={formatDuration(metrics?.total_duration_seconds)}
          subtext="Transcribed audio"
          icon={Clock}
          color="#0ea5e9"
        />
        <MetricCard
          title="Action Items"
          value={metrics?.total_action_items || 0}
          subtext={`${metrics?.pending_action_items || 0} pending commitments`}
          icon={CheckSquare}
          color="#8b5cf6"
        />
        <MetricCard
          title="Verified Decisions"
          value={metrics?.verified_decisions || 0}
          subtext="Backed by transcript evidence"
          icon={ShieldCheck}
          color="var(--success)"
        />
      </div>

      {/* Recent Meetings Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Recent Meetings</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Latest recordings ingested and analyzed
            </p>
          </div>
          <button onClick={() => onNavigate('meetings')} className="btn btn-secondary btn-sm">
            <span>View All</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          {(!metrics?.recent_meetings || metrics.recent_meetings.length === 0) ? (
            <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
              <FileAudio size={40} style={{ margin: '0 auto 12px', color: 'var(--text-light)' }} />
              <p style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                No meeting recordings yet
              </p>
              <p style={{ fontSize: '0.85rem', marginBottom: 16 }}>
                Upload an audio recording to extract evidence-backed summaries, decisions and action items.
              </p>
              <button onClick={() => onNavigate('upload')} className="btn btn-primary btn-sm">
                <UploadCloud size={14} />
                <span>Upload First Recording</span>
              </button>
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Meeting Title</th>
                    <th>Date</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Decisions</th>
                    <th>Actions</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.recent_meetings.map((m) => (
                    <tr key={m.id} style={{ cursor: 'pointer' }} onClick={() => onSelectMeeting(m.id)}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {m.title}
                      </td>
                      <td>{formatDate(m.created_at)}</td>
                      <td>{formatDuration(m.duration)}</td>
                      <td>
                        <span
                          className={`badge ${
                            m.status === 'completed'
                              ? 'badge-verified'
                              : m.status === 'processing'
                              ? 'badge-primary'
                              : m.status === 'failed'
                              ? 'badge-flagged'
                              : 'badge-neutral'
                          }`}
                        >
                          {m.status}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 500 }}>{m.decision_count}</span>
                      </td>
                      <td>
                        <span>
                          {m.action_item_count} ({m.pending_action_item_count} pending)
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectMeeting(m.id);
                          }}
                          className="btn btn-secondary btn-sm"
                        >
                          <span>Open</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
