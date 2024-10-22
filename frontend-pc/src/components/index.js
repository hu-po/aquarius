import React, { useState, useEffect } from 'react';
import { API, DASHBOARD, STATS } from '../config';
import { getStatus } from '../services/api';

// ErrorBoundary Component
export const ErrorBoundary = ({ children, fallback }) => {
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleError = (error, errorInfo) => {
      console.error('Component Error:', error, errorInfo);
      setError(error);
      setHasError(true);
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return fallback || <div>Something went wrong.</div>;
  }
  return children;
};

// Dashboard Component
export const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const data = await getStatus();
        if (mounted) {
          setStatus(data);
          setError(null);
        }
      } catch (error) {
        if (mounted) {
          console.error('Error fetching status:', error);
          setError(error.message || 'Failed to load aquarium data.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, API.POLL_INTERVAL);
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
        <h1>Aquarius Dashboard</h1>
        {status?.alerts?.length > 0 && (
          <div className="alerts">
            {status.alerts.map((alert, index) => (
              <div key={index} className="alert">{alert}</div>
            ))}
          </div>
        )}
      </header>
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <LatestImage image={status?.latest_image} />
        </div>
        <div className="dashboard-section">
          <Stats reading={status?.latest_reading} />
        </div>
        <div className="dashboard-section">
          <LLMReply descriptions={status?.latest_descriptions} />
        </div>
        <div className="dashboard-section">
          <FishPositionPlot image={status?.latest_image} />
        </div>
      </div>
    </div>
  );
};

// LatestImage Component
export const LatestImage = ({ image }) => {
  const [imageError, setImageError] = useState(false);

  if (!image) {
    return (
      <div className="latest-image">
        <h2>Latest Image</h2>
        <div className="no-image-placeholder">No image available</div>
      </div>
    );
  }

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${API.BASE_URL}/images/${encodeURIComponent(filename)}`;
  };

  return (
    <div className="latest-image">
      <h2>Latest Image</h2>
      {!imageError ? (
        <img 
          src={getImageUrl(image.filepath)}
          alt="Latest aquarium capture"
          className="aquarium-image"
          onError={() => setImageError(true)}
          style={{
            maxWidth: DASHBOARD.IMAGE_MAX_WIDTH,
            maxHeight: DASHBOARD.IMAGE_MAX_HEIGHT
          }}
        />
      ) : (
        <div className="image-error">Failed to load image</div>
      )}
      <div className="image-info">
        <div>Resolution: {image.width} x {image.height}</div>
        <div>Captured: {new Date(image.timestamp).toLocaleString()}</div>
        <div>Device ID: {image.device_id}</div>
      </div>
    </div>
  );
};

// LLMReply Component
export const LLMReply = ({ descriptions }) => {
  const [selectedModel, setSelectedModel] = useState(Object.keys(descriptions || {})[0]);

  if (!descriptions || Object.keys(descriptions).length === 0) {
    return <div className="llm-reply">No AI descriptions available</div>;
  }

  return (
    <div className="llm-reply">
      <h2>AI Analysis</h2>
      <div className="model-selector">
        {Object.keys(descriptions).map((model) => (
          <button
            key={model}
            className={`model-button ${selectedModel === model ? 'active' : ''}`}
            onClick={() => setSelectedModel(model)}
          >
            {model}
          </button>
        ))}
      </div>
      <div className="description">
        {descriptions[selectedModel]}
      </div>
    </div>
  );
};

// Stats Component
export const Stats = ({ reading }) => {
  if (!reading) {
    return <div className="stats">No sensor readings available</div>;
  }

  const formatValue = (value, unit) => {
    return value ? `${value.toFixed(STATS.DECIMAL_PLACES)} ${unit}` : 'N/A';
  };

  return (
    <div className="stats">
      <h2>Sensor Readings</h2>
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

// FishPositionPlot Component
export const FishPositionPlot = ({ image }) => {
  return (
    <div className="fish-position-plot">
      <h2>Fish Movement</h2>
      <div className="placeholder">
        Fish position tracking functionality coming soon
      </div>
    </div>
  );
};