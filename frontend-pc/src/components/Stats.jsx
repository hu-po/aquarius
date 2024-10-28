import React from 'react';

const Stats = ({ reading }) => {
  if (!reading) {
    return <div className="stats">No sensor readings available</div>;
  }

  const formatValue = (value, unit) => {
    return value ? `${value.toFixed(1)} ${unit}` : 'N/A';
  };

  return (
    <div className="stats">
      <div className="stats-grid">
        <div className="stat-item">
          <label>Temperature</label>
          <span>{formatValue(reading.temperature, '°F')}</span>
        </div>
        <div className="stat-item">
          <label>pH</label>
          <span>{formatValue(reading.ph, '')}</span>
        </div>
        <div className="stat-item">
          <label>Ammonia</label>
          <span>{formatValue(reading.ammonia, 'ppm')}</span>
        </div>
        <div className="stat-item">
          <label>Nitrite</label>
          <span>{formatValue(reading.nitrite, 'ppm')}</span>
        </div>
        <div className="stat-item">
          <label>Nitrate</label>
          <span>{formatValue(reading.nitrate, 'ppm')}</span>
        </div>
      </div>
      <div className="timestamp">
        Last updated: {new Date(reading.timestamp).toLocaleString()}
      </div>
    </div>
  );
};

export default Stats;
