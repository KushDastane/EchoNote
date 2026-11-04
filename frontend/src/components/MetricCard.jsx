import React from 'react';

export default function MetricCard({ title, value, subtext, icon: Icon, color = 'var(--primary)' }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span>{title}</span>
        {Icon && <Icon size={18} style={{ color }} />}
      </div>
      <div className="metric-value">{value}</div>
      {subtext && <div className="metric-sub">{subtext}</div>}
    </div>
  );
}
