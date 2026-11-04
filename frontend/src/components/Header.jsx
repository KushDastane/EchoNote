import React from 'react';
import { UploadCloud, Search as SearchIcon } from 'lucide-react';

export default function Header({ currentView, onNavigate }) {
  const titles = {
    overview: { title: 'Overview', subtitle: 'Platform activity and meeting intelligence summary' },
    meetings: { title: 'Meetings', subtitle: 'Catalog of processed recordings and discussions' },
    upload: { title: 'Upload Recording', subtitle: 'Ingest audio for transcription and structured intelligence' },
    search: { title: 'Search Intelligence', subtitle: 'Locate discussions, decisions, and action items' },
    settings: { title: 'System Settings', subtitle: 'Audio pipeline, model providers, and configuration' },
    detail: { title: 'Meeting Intelligence', subtitle: 'Evidence-backed transcript, decisions, and action items' },
  };

  const current = titles[currentView] || titles.overview;

  return (
    <header className="top-header">
      <div className="header-title">
        <h2>{current.title}</h2>
        <p>{current.subtitle}</p>
      </div>

      <div className="header-actions">
        {currentView !== 'search' && (
          <button
            onClick={() => onNavigate('search')}
            className="btn btn-secondary btn-sm"
          >
            <SearchIcon size={14} />
            <span>Search</span>
          </button>
        )}
        {currentView !== 'upload' && (
          <button
            onClick={() => onNavigate('upload')}
            className="btn btn-primary btn-sm"
          >
            <UploadCloud size={14} />
            <span>New Upload</span>
          </button>
        )}
      </div>
    </header>
  );
}
