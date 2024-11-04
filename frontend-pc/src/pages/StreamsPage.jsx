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
  const [streamsInitialized, setStreamsInitialized] = useState(false);
  const [resetCounter, setResetCounter] = useState(0);

  useEffect(() => {
    let mounted = true;
    const loadData = async () => {
      try {
        setLoading(true);
        const [deviceList, statusData] = await Promise.all([
          getDevices(),
          getStatus()
        ]);
        if (!mounted) return;
        setDevices(deviceList);
        setStatus(statusData);
        setError(null);
        setStreamsInitialized(true);
      } catch (err) {
        if (!mounted) return;
        setError(err.message || 'Failed to load data');
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadData();
    const interval = setInterval(loadData, 30000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
      setStreamsInitialized(false);
    };
  }, []);

  const handleSingleCapture = async (deviceIndex) => {
    if (pausedDevices.has(deviceIndex)) return;
    
    setPausedDevices(prev => new Set([...prev, deviceIndex]));
    try {
      await captureImage(deviceIndex);
      setSuccessMessage(`Captured image from camera ${deviceIndex}`);
    } catch (err) {
      setWarning(err.message || `Failed to capture from camera ${deviceIndex}`);
    } finally {
      setPausedDevices(prev => {
        const updated = new Set(prev);
        updated.delete(deviceIndex);
        return updated;
      });
    }
  };

  const handleResetStreams = () => {
    setStreamsInitialized(false);
    setTimeout(() => {
      setStreamsInitialized(true);
      setResetCounter(prev => prev + 1);
    }, 100);
  };

  if (loading) return <div className="loading">🔄</div>;
  if (error) return <div className="error">⚠️ {error}</div>;

  return (
    <div className="streams-page">
      <div className="streams-header">
        <button 
          className="reset-button"
          onClick={handleResetStreams}
          disabled={loading || !streamsInitialized}
        >
          🔄 reset streams
        </button>
      </div>
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
            {streamsInitialized && (
              <CameraStream 
                deviceIndex={device.index}
                isPaused={pausedDevices.has(device.index)}
                onCapture={handleSingleCapture}
                key={`stream-${device.index}-${streamsInitialized}-${resetCounter}`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default StreamsPage; 