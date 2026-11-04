import React from 'react';
import {
  LayoutDashboard,
  FileAudio,
  UploadCloud,
  Search,
  Settings as SettingsIcon,
  Activity
} from 'lucide-react';

export default function Sidebar({ currentView, onNavigate, serverHealthy }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'meetings', label: 'Meetings', icon: FileAudio },
    { id: 'upload', label: 'Upload Recording', icon: UploadCloud },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Activity size={20} />
        </div>
        <div className="brand-text">
          <h1>EchoNote</h1>
          <p>Meeting Intelligence</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator">
          <span
            className="status-dot"
            style={{ backgroundColor: serverHealthy ? 'var(--success)' : 'var(--danger)' }}
          />
          <span>{serverHealthy ? 'Engine Connected' : 'Offline'}</span>
        </div>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-light)' }}>v1.0.0</span>
      </div>
    </aside>
  );
}
