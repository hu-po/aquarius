import React, { useState, useEffect } from 'react';
import { CameraStream, LatestImage, Stats, ModelResponse } from './';
import { getDevices, getStatus, captureImage } from '../services/api';
import Life from './Life';

export const Dashboard = () => {
  const [devices, setDevices] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(null);
  const [location, setLocation] = useState(null);
  const [timezone, setTimezone] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const loadData = async () => {
      try {
        const [deviceList, statusData] = await Promise.all([
          getDevices(),
          getStatus()
        ]);
        setDevices(deviceList);
        setStatus(statusData);
        setLocation(statusData.location);
        setTimezone(statusData.timezone);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const dataInterval = setInterval(loadData, 30000);

    // Update time every second
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(dataInterval);
      clearInterval(timeInterval);
    };
  }, []);

  const handleCapture = async () => {
    setCapturing(true);
    setAnalysisProgress('Capturing images...');
    try {
      // Capture images from all active devices
      const capturePromises = devices.map(device => 
        captureImage(device.index)
      );
      await Promise.all(capturePromises);
      
      setAnalysisProgress('Analyzing images...');
      // Get updated status which includes analysis results
      const statusData = await getStatus();
      setStatus(statusData);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to capture/analyze images');
    } finally {
      setCapturing(false);
      setAnalysisProgress(null);
    }
  };

  if (loading) return <div className="loading">🔄</div>;
  if (error) return <div className="error">⚠️ {error}</div>;

  return (
    <div className="dashboard">
      {error && (
        <div className="backend-error">
          <span className="error-message">{error}</span>
        </div>
      )}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🐟</h1>
          <div className="tank-info">
            <span className="location">📍 {location || "Location not set"}</span>
            <span className="time">🕒 {currentTime.toLocaleString('en-US', { 
              timeZone: timezone || "UTC",
              dateStyle: 'medium',
              timeStyle: 'medium'
            })}</span>
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

      <div className="camera-streams">
        {devices.map(device => (
          <div key={device.index} className="stream-container">
            <h2>📸 {device.name}</h2>
            <CameraStream deviceIndex={device.index} />
            {status?.latest_images[device.index] && (
              <LatestImage image={status.latest_images[device.index]} />
            )}
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>🧠 Analysis</h2>
          <div className="brain-container">
            <button 
              className={`capture-button ${capturing ? 'capturing' : ''}`}
              onClick={handleCapture}
              disabled={capturing}
            >
              {capturing ? `${analysisProgress || '📸 ...'} ` : '📸'}
            </button>
            <ModelResponse responses={status?.latest_responses} />
          </div>
        </div>

        <div className="dashboard-section">
          <h2>🌿 Life</h2>
          <Life />
        </div>

        <div className="dashboard-section">
          <h2>🖼️ Latest Capture</h2>
          <LatestImage image={status?.latest_image} />
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
