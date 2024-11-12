import React, { useState, useEffect } from 'react';
import { AIAnalysis } from '../components';
import { getStatus, toggleScan } from '../services/api';

export const AnalysisPage = () => {
  const [scanEnabled, setScanEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

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
    setLoading(true);
    try {
      await toggleScan(!scanEnabled);
      setScanEnabled(!scanEnabled);
    } catch (err) {
      console.error('Failed to toggle scan:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-page">
      <div className="analysis-header">
        <button
          onClick={handleToggleScan}
          disabled={loading}
          className={`scan-toggle ${scanEnabled ? 'active' : ''}`}
          title={`Scheduled scan is ${scanEnabled ? 'enabled' : 'disabled'}`}
        >
          {loading ? '⏳' : scanEnabled ? '🔍' : '⏹️'}
        </button>
      </div>
      <AIAnalysis />
    </div>
  );
};

export default AnalysisPage; 