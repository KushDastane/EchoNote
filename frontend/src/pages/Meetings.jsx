import React, { useEffect, useState } from 'react';
import {
  FileAudio,
  Trash2,
  ExternalLink,
  Search,
  RefreshCw,
  Plus
} from 'lucide-react';
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
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export default function Meetings({ onSelectMeeting, onNavigate }) {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [deletingId, setDeletingId] = useState(null);

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const data = await api.getMeetings();
      setMeetings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this meeting and its recordings?')) {
      return;
    }
    try {
      setDeletingId(id);
      await api.deleteMeeting(id);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = meetings.filter((m) => {
    const matchesSearch =
      m.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.original_filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || m.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
          flexWrap: 'wrap',
          gap: 16
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 260 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 360 }}>
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
              placeholder="Search meetings by title or filename..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input"
              style={{ paddingLeft: 30 }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="select"
            style={{ width: 140 }}
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="uploaded">Uploaded</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={fetchMeetings} className="btn btn-secondary btn-sm" title="Refresh list">
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          <button onClick={() => onNavigate('upload')} className="btn btn-primary btn-sm">
            <Plus size={14} />
            <span>Upload Recording</span>
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h3 className="card-title">Meeting Catalog</h3>
            <span className="badge badge-neutral">{filtered.length} meetings</span>
          </div>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          {loading ? (
            <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading meetings...
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>
              <FileAudio size={40} style={{ margin: '0 auto 12px', color: 'var(--text-light)' }} />
              <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>No meetings found</p>
              <p style={{ fontSize: '0.85rem' }}>
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search query or filters.'
                  : 'Get started by uploading your first meeting audio.'}
              </p>
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Title & File</th>
                    <th>Created</th>
                    <th>Duration</th>
                    <th>Status</th>
                    <th>Decisions</th>
                    <th>Action Items</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((m) => (
                    <tr
                      key={m.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => onSelectMeeting(m.id)}
                    >
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {m.title}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>
                          {m.original_filename}
                        </div>
                      </td>
                      <td style={{ fontSize: '0.8125rem' }}>{formatDate(m.created_at)}</td>
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
                      <td>{m.decision_count}</td>
                      <td>
                        {m.action_item_count} ({m.pending_action_item_count} pending)
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectMeeting(m.id);
                            }}
                            className="btn btn-secondary btn-sm"
                            title="Open meeting details"
                          >
                            <ExternalLink size={12} />
                            <span>Open</span>
                          </button>
                          <button
                            onClick={(e) => handleDelete(e, m.id)}
                            disabled={deletingId === m.id}
                            className="btn btn-secondary btn-sm"
                            title="Delete meeting"
                            style={{ color: 'var(--danger)' }}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
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
