import React from 'react';
import { HelpCircle, CheckCircle2, Tag } from 'lucide-react';

export default function InsightsPanel({ summary, keyPoints = [], unresolvedQuestions = [], topics = [] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Executive Summary */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Executive Summary</h3>
        </div>
        <div className="card-body">
          <p style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
            {summary || 'No summary generated yet.'}
          </p>

          {topics && topics.length > 0 && (
            <div style={{ marginTop: 16, display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Tag size={12} /> Topics:
              </span>
              {topics.map((t, idx) => (
                <span key={idx} className="badge badge-primary" style={{ fontSize: '0.7rem' }}>
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Key Discussion Points */}
      {keyPoints && keyPoints.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Key Discussion Points</h3>
            <span className="badge badge-neutral">{keyPoints.length} points</span>
          </div>
          <div className="card-body" style={{ padding: '12px 20px' }}>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {keyPoints.map((point, idx) => (
                <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: '0.875rem' }}>
                  <CheckCircle2 size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: 3 }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Unresolved Questions & Blockers */}
      {unresolvedQuestions && unresolvedQuestions.length > 0 && (
        <div className="card" style={{ borderColor: 'var(--warning-border)' }}>
          <div className="card-header" style={{ backgroundColor: 'var(--warning-bg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <HelpCircle size={16} color="var(--warning)" />
              <h3 className="card-title" style={{ color: 'var(--warning)', fontSize: '0.9rem' }}>
                Unresolved Questions & Open Items
              </h3>
            </div>
            <span className="badge badge-unverified">{unresolvedQuestions.length} open</span>
          </div>
          <div className="card-body" style={{ padding: '12px 20px' }}>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {unresolvedQuestions.map((q, idx) => (
                <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--warning)', fontWeight: 700, marginTop: 1 }}>?</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
