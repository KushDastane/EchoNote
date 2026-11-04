import React, { useState, useEffect } from 'react';
import {
  Search as SearchIcon,
  FileAudio,
  CheckCircle2,
  CheckSquare,
  MessageSquare,
  ArrowUpRight,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';

function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function Search({ onSelectMeeting }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all'); // all, title, transcript, decision, action_item

  const performSearch = async (q) => {
    if (!q || !q.trim()) {
      setResults([]);
      return;
    }
    try {
      setLoading(true);
      const res = await api.search(q);
      setResults(res.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const filteredResults = results.filter((r) =>
    activeFilter === 'all' ? true : r.type === activeFilter
  );

  const getResultIcon = (type) => {
    switch (type) {
      case 'title':
        return <FileAudio size={16} color="var(--primary)" />;
      case 'decision':
        return <CheckCircle2 size={16} color="var(--success)" />;
      case 'action_item':
        return <CheckSquare size={16} color="#8b5cf6" />;
      default:
        return <MessageSquare size={16} color="var(--text-muted)" />;
    }
  };

  return (
    <div style={{ maxWidth: 840, margin: '0 auto' }}>
      {/* Search Header */}
      <div style={{ marginBottom: 24, textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
          Search Meeting Intelligence
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Query across meeting titles, spoken transcript excerpts, confirmed decisions, and action items.
        </p>
      </div>

      {/* Search Input Bar */}
      <div
        className="card"
        style={{
          padding: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 16,
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <SearchIcon size={20} style={{ marginLeft: 12, color: 'var(--text-light)' }} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by keywords, decisions, speakers, tasks, or commitments..."
          style={{
            border: 'none',
            outline: 'none',
            fontSize: '1rem',
            width: '100%',
            fontFamily: 'inherit',
            color: 'var(--text-primary)'
          }}
          autoFocus
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="btn btn-secondary btn-sm"
            style={{ marginRight: 8, padding: '4px 10px' }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { id: 'all', label: 'All Results' },
          { id: 'decision', label: 'Decisions' },
          { id: 'action_item', label: 'Action Items' },
          { id: 'transcript', label: 'Transcripts' },
          { id: 'title', label: 'Meeting Titles' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveFilter(tab.id)}
            className={`btn btn-secondary btn-sm ${activeFilter === tab.id ? 'btn-primary' : ''}`}
            style={{ fontSize: '0.75rem', borderRadius: 9999 }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Results */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h3 className="card-title">Search Results</h3>
            <span className="badge badge-neutral">{filteredResults.length} matches</span>
          </div>
        </div>

        <div className="card-body" style={{ padding: 16 }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '36px 0', color: 'var(--text-muted)' }}>
              Searching intelligence database...
            </div>
          ) : !query ? (
            <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)' }}>
              <SearchIcon size={40} style={{ margin: '0 auto 12px', color: 'var(--text-light)' }} />
              <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Enter a keyword to search</p>
              <p style={{ fontSize: '0.85rem' }}>
                Search across all your processed meetings, decisions, and action items.
              </p>
            </div>
          ) : filteredResults.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)' }}>
              <p style={{ fontWeight: 500, color: 'var(--text-primary)' }}>No results found for "{query}"</p>
              <p style={{ fontSize: '0.85rem' }}>Try searching for a different phrase or term.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {filteredResults.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => onSelectMeeting(item.meeting_id)}
                  style={{
                    padding: 14,
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    backgroundColor: 'var(--bg-surface)',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'var(--bg-surface)')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {getResultIcon(item.type)}
                      <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>
                        {item.type.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        {item.meeting_title}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 500 }}>
                      {item.timestamp !== null && item.timestamp !== undefined && (
                        <span>{formatTime(item.timestamp)}</span>
                      )}
                      <ArrowUpRight size={14} />
                    </div>
                  </div>

                  <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                    {item.text}
                  </p>

                  {item.evidence && (
                    <div className="evidence-quote" style={{ marginTop: 6, fontSize: '0.75rem' }}>
                      <span>Evidence: "{item.evidence}"</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
