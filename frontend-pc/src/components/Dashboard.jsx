import React, { useState, useEffect } from 'react';
import { CameraStream, Stats, AIAnalysis } from './';
import { getDevices, getStatus, captureImage, Analyze } from '../services/api';
import Life from './Life';

export const Dashboard = () => {
  const [devices, setDevices] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pausedDevices, setPausedDevices] = useState(new Set());
  const [warning, setWarning] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loadingStates, setLoadingStates] = useState({
    devices: false,
    capture: false
  });
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
    const dataInterval = setInterval(loadData, 30000);
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(dataInterval);
      clearInterval(timeInterval);
    };
  }, []);

  const handleSingleCapture = async (deviceIndex) => {
    setPausedDevices(new Set([deviceIndex]));
    setWarning(null);
    setSuccessMessage(null);
    
    try {
      const currentDevices = await getDevices();
      const device = currentDevices.find(d => d.index === deviceIndex);
      
      if (!device?.active) {
        setWarning('Selected camera is not active. Please check camera connection.');
        return;
      }

      // Pause stream for 500ms to allow capture of image
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const captureResult = await captureImage(deviceIndex);
      if (!captureResult) {
        setWarning(`Failed to capture from camera ${deviceIndex}`);
        return;
      }

      // Wait for backend to process image
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const statusData = await getStatus();
      setStatus(statusData);
      setSuccessMessage(`Successfully captured image from camera ${deviceIndex}`);
      
      setTimeout(() => setSuccessMessage(null), 3000);

    } catch (error) {
      setWarning(error.message);
    } finally {
      setPausedDevices(prev => {
        const next = new Set(prev);
        next.delete(deviceIndex);
        return next;
      });
    }
  };

  if (loading) return <div className="loading">🔄</div>;
  if (error) return <div className="error">⚠️ {error}</div>;

  return (
    <div className="dashboard">
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
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🐟</h1>
          <div className="tank-info">
            <span className="location">📍 {status?.location || "Location not set"}</span>
            <span className="time">🕒 {currentTime.toLocaleString('en-US', { 
              timeZone: status?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
              dateStyle: 'medium',
              timeStyle: 'medium'
            })}</span>
          </div>
          <div className="header-controls">
          </div>
        </div>
        {status?.alerts?.length > 0 && (
          <div className="alerts">
            {status.alerts.map((alert, index) => (
              <div key={index} className="alert">⚠️ {alert}</div>
            ))}
          </div>
        )}
      </header>

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

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>🧠 Analysis</h2>
          <div className="brain-container">
            <AIAnalysis analyses={status?.analyses} />
          </div>
        </div>

        <div className="dashboard-section">
          <h2>🌿 Life</h2>
          <Life />
        </div>

        <div className="dashboard-section">
          <h2>📈 Stats</h2>
          <Stats reading={status?.latest_reading} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
