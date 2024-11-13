import React, { useState, useEffect } from 'react';
import { getStatus } from '../services/api';

const LocationTime = () => {
  const [status, setStatus] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await getStatus();
        setStatus(statusData);
        setError(null);
      } catch (err) {
        setError(err.message);
      }
    };

    loadStatus();
    const statusInterval = setInterval(loadStatus, 30000);
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(timeInterval);
    };
  }, []);

  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="location-time">
      <span className="location">📍 {status?.location || "Location not set"}</span>
      <span className="time">🕒 {currentTime.toLocaleString('en-US', { 
        timeZone: status?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
        dateStyle: 'medium',
        timeStyle: 'medium'
      })}</span>
    </div>
  );
};

export default LocationTime; 