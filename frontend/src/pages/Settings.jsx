import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  CheckCircle2,
  AlertTriangle,
  Server,
  Cpu,
  Brain,
  Sliders,
  Database,
  RefreshCw
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      console.error(err);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div style={{ maxWidth: 780, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            System Settings & Diagnostics
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Inspect pipeline dependencies, speech recognition engine, and intelligence providers.
          </p>
        </div>

        <button onClick={fetchHealth} className="btn btn-secondary btn-sm">
          <RefreshCw size={14} />
          <span>Refresh Status</span>
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* Diagnostic Status Card */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Server size={18} color="var(--primary)" />
              <h3 className="card-title">Runtime Diagnostics</h3>
            </div>
            <span
              className={`badge ${
                health?.status === 'healthy' ? 'badge-verified' : 'badge-flagged'
              }`}
            >
              {health?.status === 'healthy' ? 'System Operational' : 'Degraded'}
            </span>
          </div>

          <div className="card-body">
            {loading ? (
              <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                Checking runtime diagnostics...
              </div>
            ) : !health ? (
              <div style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={18} />
                <span>Backend service is not responding. Please verify that the FastAPI backend server is running.</span>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                {/* Database */}
                <div style={{ padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', backgroundColor: '#fafbfc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Database size={14} /> Database
                    </span>
                    <span className="badge badge-verified">{health.database}</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    SQLite (Local Storage)
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    PostgreSQL-compatible SQLAlchemy schema
                  </div>
                </div>

                {/* FFmpeg */}
                <div style={{ padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', backgroundColor: '#fafbfc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Cpu size={14} /> FFmpeg Audio Engine
                    </span>
                    <span className={`badge ${health.ffmpeg?.available ? 'badge-verified' : 'badge-flagged'}`}>
                      {health.ffmpeg?.available ? 'Available' : 'Missing'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={health.ffmpeg?.resolved_path}>
                    {health.ffmpeg?.resolved_path || 'ffmpeg'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    16kHz mono audio normalization
                  </div>
                </div>

                {/* Whisper */}
                <div style={{ padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', backgroundColor: '#fafbfc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Sliders size={14} /> Whisper Speech Engine
                    </span>
                    <span className="badge badge-primary">{health.ai?.whisper_model}</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    Device: {health.ai?.whisper_device?.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    Chunked transcription with offset preservation
                  </div>
                </div>

                {/* LLM Intelligence */}
                <div style={{ padding: 14, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', backgroundColor: '#fafbfc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Brain size={14} /> Intelligence Provider
                    </span>
                    <span className="badge badge-primary" style={{ textTransform: 'uppercase' }}>
                      {health.ai?.llm_provider}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                    Model: {health.ai?.llm_model}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    Strict JSON schema with evidence validation
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Guide Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">LLM Provider Configuration</h3>
          </div>
          <div className="card-body" style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <p style={{ marginBottom: 12 }}>
              EchoNote uses a modular LLM provider abstraction. You can configure which model is used by editing your <code>backend/.env</code> file:
            </p>

            <div style={{ backgroundColor: '#1e293b', color: '#f8fafc', padding: 14, borderRadius: 'var(--radius-md)', fontFamily: 'monospace', fontSize: '0.8rem', marginBottom: 16 }}>
              <div># For Zero-Cost Offline Testing / Heuristic Analysis (Default)</div>
              <div>LLM_PROVIDER=mock</div>
              <br />
              <div># For OpenAI GPT-4o / GPT-4o-mini</div>
              <div>LLM_PROVIDER=openai</div>
              <div>LLM_MODEL=gpt-4o-mini</div>
              <div>LLM_API_KEY=sk-...</div>
              <br />
              <div># For Google Gemini</div>
              <div>LLM_PROVIDER=gemini</div>
              <div>LLM_MODEL=gemini-1.5-flash</div>
              <div>LLM_API_KEY=AIzaSy...</div>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Note: Changes to <code>backend/.env</code> take effect on restarting the backend service. Never commit real API keys to version control.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
