import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Overview from './pages/Overview';
import Meetings from './pages/Meetings';
import UploadRecording from './pages/UploadRecording';
import MeetingDetail from './pages/MeetingDetail';
import Search from './pages/Search';
import Settings from './pages/Settings';
import { api } from './services/api';

export default function App() {
  const [currentView, setCurrentView] = useState('overview');
  const [selectedMeetingId, setSelectedMeetingId] = useState(null);
  const [serverHealthy, setServerHealthy] = useState(false);

  // Parse URL hash on mount or change
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('meeting/')) {
        const id = hash.replace('meeting/', '');
        setSelectedMeetingId(id);
        setCurrentView('detail');
      } else if (['overview', 'meetings', 'upload', 'search', 'settings'].includes(hash)) {
        setCurrentView(hash);
        setSelectedMeetingId(null);
      }
    };

    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Check backend health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setServerHealthy(res.status === 'healthy');
      } catch (err) {
        setServerHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const navigateTo = (view, meetingId = null) => {
    if (view === 'detail' && meetingId) {
      window.location.hash = `meeting/${meetingId}`;
      setSelectedMeetingId(meetingId);
      setCurrentView('detail');
    } else {
      window.location.hash = view;
      setCurrentView(view);
      setSelectedMeetingId(null);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        currentView={currentView}
        onNavigate={(view) => navigateTo(view)}
        serverHealthy={serverHealthy}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Header
          currentView={currentView}
          onNavigate={(view) => navigateTo(view)}
        />

        <main className="page-content">
          {currentView === 'overview' && (
            <Overview
              onNavigate={(view) => navigateTo(view)}
              onSelectMeeting={(id) => navigateTo('detail', id)}
            />
          )}

          {currentView === 'meetings' && (
            <Meetings
              onNavigate={(view) => navigateTo(view)}
              onSelectMeeting={(id) => navigateTo('detail', id)}
            />
          )}

          {currentView === 'upload' && (
            <UploadRecording
              onSelectMeeting={(id) => navigateTo('detail', id)}
              onUploadComplete={(id) => {}}
            />
          )}

          {currentView === 'detail' && selectedMeetingId && (
            <MeetingDetail
              meetingId={selectedMeetingId}
              onBack={() => navigateTo('meetings')}
            />
          )}

          {currentView === 'search' && (
            <Search
              onSelectMeeting={(id) => navigateTo('detail', id)}
            />
          )}

          {currentView === 'settings' && (
            <Settings />
          )}
        </main>
      </div>
    </div>
  );
}
