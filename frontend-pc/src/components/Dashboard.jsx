import React, { useState, useEffect } from 'react';
import { CameraStream, LatestImage, Stats, LLMReply } from './';
import { getDevices, getStatus, captureImage } from '../services/api';

export const Dashboard = () => {
  const [devices, setDevices] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);

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

  const handleCapture = async () => {
    setCapturing(true);
    try {
      await captureImage(0);
      const statusData = await getStatus();
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to capture image');
    } finally {
      setCapturing(false);
    }
  };

  if (loading) return <div className="loading">🔄</div>;
  if (error) return <div className="error">⚠️ {error}</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🐟</h1>
        </div>
        {status?.alerts?.length > 0 && (
          <div className="alerts">
            {status.alerts.map((alert, index) => (
              <div key={index} className="alert">⚠️ {alert}</div>
            ))}
          </div>
        )}
      </header>

      <div className="camera-streams">
        {devices.map(device => (
          <div key={device.index} className="stream-container">
            <h2>📸 {device.name}</h2>
            <CameraStream deviceIndex={device.index} />
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>🖼️ Latest Capture</h2>
          <LatestImage image={status?.latest_image} />
        </div>

        <div className="dashboard-section">
          <h2>📈 Stats</h2>
          <Stats reading={status?.latest_reading} />
        </div>

        <div className="dashboard-section">
          <h2>🧠 Analysis</h2>
          <div className="brain-container">
            <button 
              className={`capture-button ${capturing ? 'capturing' : ''}`}
              onClick={handleCapture}
              disabled={capturing}
            >
              {capturing ? '📸 ...' : '📸'}
            </button>
            <LLMReply descriptions={status?.latest_descriptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
