const API_BASE = '/api';

export const api = {
  // Health & System
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to retrieve system health');
    return res.json();
  },

  // Dashboard Metrics
  async getMetrics() {
    const res = await fetch(`${API_BASE}/meetings/metrics`);
    if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
    return res.json();
  },

  // Meetings CRUD
  async getMeetings() {
    const res = await fetch(`${API_BASE}/meetings`);
    if (!res.ok) throw new Error('Failed to fetch meetings list');
    return res.json();
  },

  async getMeeting(id) {
    const res = await fetch(`${API_BASE}/meetings/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch meeting ${id}`);
    return res.json();
  },

  async deleteMeeting(id) {
    const res = await fetch(`${API_BASE}/meetings/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error(`Failed to delete meeting ${id}`);
    return true;
  },

  async updateActionItem(meetingId, actionId, data) {
    const res = await fetch(`${API_BASE}/meetings/${meetingId}/actions/${actionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to update action item');
    return res.json();
  },

  // Audio Streaming URL
  getAudioUrl(meetingId) {
    return `${API_BASE}/meetings/${meetingId}/audio`;
  },

  // Upload & Processing
  async uploadRecording(file, title, autoProcess = true) {
    const formData = new FormData();
    formData.append('file', file);
    if (title && title.trim()) {
      formData.append('title', title.trim());
    }
    formData.append('auto_process', autoProcess.toString());

    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async triggerProcessing(meetingId) {
    const res = await fetch(`${API_BASE}/process/${meetingId}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Failed to trigger processing');
    return res.json();
  },

  async getProcessingStatus(meetingId) {
    const res = await fetch(`${API_BASE}/status/${meetingId}`);
    if (!res.ok) throw new Error('Failed to fetch processing status');
    return res.json();
  },

  // Search
  async search(query) {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('Failed to execute search');
    return res.json();
  }
};
