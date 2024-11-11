import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { getStatus, toggleScan } from '../services/api';

export const Layout = () => {
  const [status, setStatus] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [scanEnabled, setScanEnabled] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await getStatus();
        setStatus(statusData);
        setScanEnabled(statusData?.scan_enabled || false);
      } catch (err) {
        console.error('Failed to load status:', err);
      }
    };

    loadStatus();
    const statusInterval = setInterval(loadStatus, 30000);
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(timeInterval);
    };
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
    <div className="app-container">
      <nav className="main-nav">
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📷
          </NavLink>
          <NavLink to="/analysis" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🧠
          </NavLink>
          <NavLink to="/info" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📝
          </NavLink>
          <NavLink to="/robot" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🤖
          </NavLink>
          <button
            onClick={handleToggleScan}
            disabled={loading}
            className={`scan-toggle ${scanEnabled ? 'active' : ''}`}
            title={`Scheduled scan is ${scanEnabled ? 'enabled' : 'disabled'}`}
          >
            {loading ? '⏳' : scanEnabled ? '🔍' : '⏹️'}
          </button>
        </div>
        <div className="tank-info">
          <span className="location">📍 {status?.location || "Location not set"}</span>
          <span className="time">🕒 {currentTime.toLocaleString('en-US', { 
            timeZone: status?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
            dateStyle: 'medium',
            timeStyle: 'medium'
          })}</span>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout; 