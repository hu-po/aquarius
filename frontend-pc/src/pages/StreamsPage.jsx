import React, { useState, useEffect } from 'react';
import { CameraStream } from '../components';
import { getDevices, getStatus, captureImage } from '../services/api';

export const StreamsPage = () => {
  const [devices, setDevices] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pausedDevices, setPausedDevices] = useState(new Set());
  const [warning, setWarning] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [deviceList, statusData] = await Promise.all([
          getDevices(),
          getStatus()
        ]);
        setDevices(deviceList);
        setStatus(statusData);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSingleCapture = async (deviceIndex) => {
    // Reference existing capture logic from Dashboard.jsx
    // Lines 49-90 from Dashboard.jsx
  };

  if (loading) return <div className="loading">🔄</div>;
  if (error) return <div className="error">⚠️ {error}</div>;

  return (
    <div className="streams-page">
      {warning && (
        <div className="warning-banner">
          ⚠️ {warning}
          <button onClick={() => setWarning(null)} className="close-warning">×</button>
        </div>
      )}
      {successMessage && (
        <div className="success-banner">
          ✅ {successMessage}
          <button onClick={() => setSuccessMessage(null)} className="close-warning">×</button>
        </div>
      )}
      <div className="streams-grid">
        {devices.map(device => (
          <div key={device.index} className="stream-container">
            <div className="stream-header">
              <h2>📷 cam{device.index}</h2>
              <button 
                className={`capture-button ${pausedDevices.has(device.index) ? 'capturing' : ''}`}
                onClick={() => handleSingleCapture(device.index)}
                disabled={pausedDevices.has(device.index)}
              >
                {pausedDevices.has(device.index) ? '📸 ...' : '📸'}
              </button>
            </div>
            <CameraStream 
              deviceIndex={device.index}
              isPaused={pausedDevices.has(device.index)}
              onCapture={handleSingleCapture}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default StreamsPage; 