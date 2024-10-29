import React, { useState, useEffect } from 'react';
import { CameraStream, LatestImage, Stats, AIResponse } from './';
import { getDevices, getStatus, captureImage } from '../services/api';
import Life from './Life';

export const Dashboard = () => {
  const [devices, setDevices] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(null);
  const [pausedDevices, setPausedDevices] = useState(new Set());
  const [warning, setWarning] = useState(null);

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

    return () => {
      clearInterval(dataInterval);
    };
  }, []);

  const handleCapture = async () => {
    setCapturing(true);
    setAnalysisProgress('Preparing to capture...');
    setWarning(null);
    
    try {
      const currentDevices = await getDevices();
      const activeDevices = currentDevices.filter(d => d.active);
      
      if (activeDevices.length === 0) {
        setWarning('No active camera devices found. Please check camera connections.');
        return;
      }

      setPausedDevices(new Set(activeDevices.map(d => d.index)));
      await new Promise(resolve => setTimeout(resolve, 500));

      setAnalysisProgress('Capturing images...');
      const captureResults = await Promise.allSettled(
        activeDevices.map(device => captureImage(device.index))
      );

      const failures = captureResults.filter(r => r.status === 'rejected')
        .map(r => r.reason.message);
      
      if (failures.length > 0) {
        setWarning(`Some captures failed: ${failures.join(', ')}`);
        if (failures.length === activeDevices.length) {
          return;
        }
      }

      setAnalysisProgress('Processing with AI models...');
      let analysisComplete = false;
      let attempts = 0;
      
      while (!analysisComplete && attempts < 30) {
        const statusData = await getStatus();
        if (statusData.latest_responses?.length > 0) {
          analysisComplete = true;
          setStatus(statusData);
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
      }

      if (!analysisComplete) {
        setWarning('Analysis timed out. Some results may be missing.');
      }

    } catch (err) {
      setWarning(err.message || 'Failed to capture/analyze images');
    } finally {
      setPausedDevices(new Set());
      setCapturing(false);
      setAnalysisProgress(null);
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
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🐟</h1>
          <div className="tank-info">
            <span className="location">📍 {status?.location || "Location not set"}</span>
            <span className="time">🕒 {new Date().toLocaleString('en-US', { 
              timeZone: status?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
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

      <div className="streams-grid">
        {devices.map(device => (
          <div key={device.index} className="stream-container">
            <h2>{device.name}</h2>
            <CameraStream 
              deviceIndex={device.index}
              isPaused={pausedDevices.has(device.index)}
            />
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
            <AIResponse responses={status?.latest_responses} />
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
