import React from 'react';
import { CheckCircle2, Clock, User, Calendar, AlertTriangle, XCircle, ArrowUpRight } from 'lucide-react';

function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function ActionItemsList({
  actionItems = [],
  onToggleStatus,
  onJumpToEvidence
}) {
  const getStatusBadge = (status) => {
    switch (status) {
      case 'verified':
        return (
          <span className="badge badge-verified">
            <CheckCircle2 size={12} /> Verified
          </span>
        );
      case 'flagged':
        return (
          <span className="badge badge-flagged">
            <XCircle size={12} /> Flagged
          </span>
        );
      default:
        return (
          <span className="badge badge-unverified">
            <AlertTriangle size={12} /> Unverified
          </span>
        );
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3 className="card-title">Action Items & Commitments</h3>
          <span className="badge badge-neutral">{actionItems.length} items</span>
        </div>
      </div>

      <div className="card-body" style={{ padding: '16px 20px' }}>
        {actionItems.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
            No action items extracted from this meeting.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {actionItems.map((act) => {
              const isCompleted = act.status === 'completed';

              return (
                <div
                  key={act.id}
                  style={{
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    padding: 16,
                    backgroundColor: isCompleted ? '#fafbfc' : 'var(--bg-surface)',
                    opacity: isCompleted ? 0.75 : 1
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                    <input
                      type="checkbox"
                      checked={isCompleted}
                      onChange={() => onToggleStatus(act.id, isCompleted ? 'pending' : 'completed')}
                      style={{
                        marginTop: 4,
                        width: 16,
                        height: 16,
                        cursor: 'pointer',
                        accentColor: 'var(--primary)'
                      }}
                    />

                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                        {getStatusBadge(act.validation_status)}

                        {/* Owner Badge */}
                        <span
                          className="badge"
                          style={{
                            backgroundColor: act.owner && act.owner !== 'Not specified' ? '#f1f5f9' : '#f8fafc',
                            color: act.owner && act.owner !== 'Not specified' ? 'var(--text-primary)' : 'var(--text-light)',
                            border: '1px solid var(--border-color)'
                          }}
                        >
                          <User size={12} /> {act.owner || 'Not specified'}
                        </span>

                        {/* Deadline Badge */}
                        <span
                          className="badge"
                          style={{
                            backgroundColor: act.deadline && act.deadline !== 'Not specified' ? '#f1f5f9' : '#f8fafc',
                            color: act.deadline && act.deadline !== 'Not specified' ? 'var(--text-primary)' : 'var(--text-light)',
                            border: '1px solid var(--border-color)'
                          }}
                        >
                          <Calendar size={12} /> {act.deadline || 'Not specified'}
                        </span>
                      </div>

                      <p
                        style={{
                          fontSize: '0.925rem',
                          fontWeight: 500,
                          color: isCompleted ? 'var(--text-muted)' : 'var(--text-primary)',
                          textDecoration: isCompleted ? 'line-through' : 'none'
                        }}
                      >
                        {act.task}
                      </p>

                      {act.evidence && (
                        <div className="evidence-quote">
                          <div className="evidence-header">
                            <span>Transcript Evidence Excerpt</span>
                          </div>
                          <span>"{act.evidence}"</span>
                        </div>
                      )}
                    </div>

                    {act.timestamp !== null && act.timestamp !== undefined && (
                      <button
                        onClick={() => onJumpToEvidence(act.timestamp, act.evidence)}
                        className="btn btn-secondary btn-sm"
                        title="Jump to audio & transcript excerpt"
                        style={{ fontSize: '0.75rem', gap: 4, alignSelf: 'flex-start' }}
                      >
                        <span>{formatTime(act.timestamp)}</span>
                        <ArrowUpRight size={12} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
