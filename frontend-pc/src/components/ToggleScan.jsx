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
    <button
      onClick={handleToggleScan}
      disabled={scanLoading}
      className={scanEnabled ? 'active' : ''}
    >
      {scanLoading ? '🔍 ... ⏳' : scanEnabled ? '🔍 Auto Scan On ✅' : '🔍 Auto Scan Off ❌'}
    </button>
  );
};

export default ToggleScan; 