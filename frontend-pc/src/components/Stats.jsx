import React from 'react';

const Stats = ({ reading }) => {
  if (!reading) {
    return <div className="stats">No sensor readings available</div>;
  }

  return (
    <div className="stats">
      <div className="stats-grid">
        <div className="stat-item">
          <label>Temperature</label>
          <span>{reading.temperature ? `${reading.temperature.toFixed(1)}°F` : 'N/A'}</span>
        </div>
      </div>
      <div className="timestamp">
        Last updated: {new Date(reading.timestamp).toLocaleString()}
      </div>
    </div>
  );
};

export default Stats;
