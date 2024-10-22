import React, { useState, useEffect, Suspense } from 'react';
import { getStatus } from '../../services/api';
import LatestImage from '../LatestImage';
import LLMReply from '../LLMReply';
import Stats from '../Stats';
import FishPositionPlot from '../FishPositionPlot';
import ErrorBoundary from './ErrorBoundary';
import './Dashboard.css';

const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdateTime, setLastUpdateTime] = useState(null);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const data = await getStatus();
        if (mounted) {
          setStatus(data);
          setLastUpdateTime(new Date());
          setError(null);
        }
      } catch (error) {
        if (mounted) {
          console.error('Error fetching status:', error);
          setError(error.message || 'Failed to load aquarium data.');
          // Don't clear previous status on error to maintain stale-while-revalidate pattern
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };
  
    fetchData();
    const interval = setInterval(fetchData, 30000);
    
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

export default Dashboard;