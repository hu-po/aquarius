import React, { useState, useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { getStatus } from '../services/api';

export const Layout = () => {
  const [status, setStatus] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await getStatus();
        setStatus(statusData);
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

  return (
    <div className="app-container">
      <nav className="main-nav">
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            📷 Streams
          </NavLink>
          <NavLink to="/analysis" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            🧠 Analysis
          </NavLink>
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