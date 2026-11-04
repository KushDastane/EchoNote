import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ArrowUpRight } from 'lucide-react';

function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function DecisionsList({ decisions = [], onJumpToEvidence }) {
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
          <h3 className="card-title">Agreed Decisions</h3>
          <span className="badge badge-neutral">{decisions.length} recorded</span>
        </div>
      </div>

      <div className="card-body" style={{ padding: '16px 20px' }}>
        {decisions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
            No confirmed decisions identified in this recording.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {decisions.map((dec) => (
              <div
                key={dec.id}
                style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: 16,
                  backgroundColor: 'var(--bg-surface)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      {getStatusBadge(dec.validation_status)}
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Confidence: {Math.round(dec.confidence * 100)}%
                      </span>
                      {dec.speaker && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-light)' }}>
                          • {dec.speaker}
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.925rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {dec.description}
                    </p>
                  </div>

                  {dec.timestamp !== null && dec.timestamp !== undefined && (
                    <button
                      onClick={() => onJumpToEvidence(dec.timestamp, dec.evidence)}
                      className="btn btn-secondary btn-sm"
                      title="Jump to audio & transcript excerpt"
                      style={{ fontSize: '0.75rem', gap: 4 }}
                    >
                      <span>{formatTime(dec.timestamp)}</span>
                      <ArrowUpRight size={12} />
                    </button>
                  )}
                </div>

                {dec.evidence && (
                  <div className="evidence-quote">
                    <div className="evidence-header">
                      <span>Supporting Transcript Evidence</span>
                    </div>
                    <span>"{dec.evidence}"</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
