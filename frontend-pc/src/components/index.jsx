import React, { useState, useEffect } from 'react';
import { getStatus, captureImage, getDevices } from '../services/api';
import CameraStream from './CameraStream';

const POLL_INTERVAL = 30000; // 30 seconds default

export const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(0);
  const [loadingDevices, setLoadingDevices] = useState(true);

  const fetchDevices = async () => {
    try {
      const deviceList = await getDevices();
      setDevices(deviceList);
      if (deviceList.length > 0) {
        setSelectedDevice(deviceList[0].index);
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
      setError('Failed to load camera devices.');
    } finally {
      setLoadingDevices(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const data = await getStatus();
      setStatus(data);
      setError(null);
    } catch (error) {
      console.error('Error fetching status:', error);
      setError(error.message || 'Failed to load aquarium data.');
    } finally {
      setLoading(false);
    }
  };

  const handleCapture = async () => {
    setCapturing(true);
    try {
      await captureImage(selectedDevice);
      await fetchStatus();
    } catch (error) {
      console.error('Error capturing image:', error);
      setError(error.message || 'Failed to capture image.');
    } finally {
      setCapturing(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      if (mounted) {
        await fetchStatus();
      }
    };

    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading && !status) {
    return <div className="dashboard loading">Loading...</div>;
  }

  if (error) {
    return <div className="dashboard error">{error}</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🐟</h1>
          <div className="header-controls">
            <button 
              className={`capture-button ${capturing ? 'capturing' : ''}`}
              onClick={handleCapture}
              disabled={capturing || devices.length === 0}
            >
              {capturing ? 'Capturing...' : '📸'}
            </button>
          </div>
        </div>
        {status?.alerts?.length > 0 && (
          <div className="alerts">
            {status.alerts.map((alert, index) => (
              <div key={index} className="alert">{alert}</div>
            ))}
          </div>
        )}
      </header>
      <div className="camera-streams">
        <div className="stream-container">
          <h2>Camera 0</h2>
          <CameraStream deviceIndex={0} />
        </div>
        <div className="stream-container">
          <h2>Camera 1</h2>
          <CameraStream deviceIndex={1} />
        </div>
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>🖼️</h2>
          <LatestImage image={status?.latest_image} />
        </div>
        <div className="dashboard-section">
          <h2>📈</h2>
          <Stats reading={status?.latest_reading} />
        </div>
        <div className="dashboard-section">
          <h2>🧠</h2>
          <LLMReply descriptions={status?.latest_descriptions} />
        </div>
      </div>
    </div>
  );
};

export const LatestImage = ({ image }) => {
  const [imageError, setImageError] = useState(false);
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  if (!image) {
    return <div className="latest-image">No image available</div>;
  }

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${BACKEND_URL}/images/${encodeURIComponent(filename)}`;
  };

  return (
    <div className="latest-image">
      {!imageError ? (
        <img 
          src={getImageUrl(image.filepath)}
          alt="Latest aquarium capture"
          className="aquarium-image"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="image-error">Failed to load image</div>
      )}
      <div className="image-info">
        <div>Captured: {new Date(image.timestamp).toLocaleString()}</div>
      </div>
    </div>
  );
};

export const LLMReply = ({ descriptions }) => {
  if (!descriptions || Object.keys(descriptions).length === 0) {
    return <div className="llm-reply">No AI descriptions available</div>;
  }

  const modelIcons = {
    'claude': '🔮',
    'gpt4o-mini': '🤖',
    'gemini': '💫'
  };

  return (
    <div className="llm-reply">
      {Object.entries(descriptions).map(([model, description]) => (
        <div key={model} className="model-output">
          <div className="model-header">
            <span className="model-icon">{modelIcons[model] || '🔍'}</span>
            <span className="model-name">{model}</span>
          </div>
          <div className="description">
            {description}
          </div>
        </div>
      ))}
    </div>
  );
};

export const Stats = ({ reading }) => {
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