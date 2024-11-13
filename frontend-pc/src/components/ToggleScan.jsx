import React, { useState, useEffect } from 'react';
import { getStatus, toggleScan } from '../services/api';

const ToggleScan = () => {
  const [scanEnabled, setScanEnabled] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await getStatus();
        setScanEnabled(statusData?.scan_enabled || false);
      } catch (err) {
        console.error('Failed to load status:', err);
      }
    };
    loadStatus();
    const statusInterval = setInterval(loadStatus, 30000);
    return () => clearInterval(statusInterval);
  }, []);

  const handleToggleScan = async () => {
    setScanLoading(true);
    try {
      await toggleScan(!scanEnabled);
      setScanEnabled(!scanEnabled);
    } catch (err) {
      console.error('Failed to toggle scan:', err);
    } finally {
      setScanLoading(false);
    }
  };

  return (
    <div className="scan-toggle-container">
      <div 
        className={`scan-rocker ${scanLoading ? 'loading' : ''}`}
        onClick={!scanLoading ? handleToggleScan : undefined}
      >
        <div className={`rocker-switch ${scanEnabled ? 'on' : 'off'}`}>
          <div className="switch-state off">
            <span>💤</span>
            <span>OFF</span>
          </div>
          <div className="switch-state on">
            <span>📡</span>
            <span>ON</span>
          </div>
          <div className="switch-indicator" />
        </div>
      </div>
    </div>
  );
};

export default ToggleScan; 