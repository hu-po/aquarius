import React, { useState, useEffect } from 'react';
import { getStatus } from '../../services/api';
import LatestImage from '../LatestImage';
import LLMReply from '../LLMReply';
import Stats from '../Stats';
import FishPositionPlot from '../FishPositionPlot';
import './Dashboard.css';

const Dashboard = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getStatus();
        setStatus(data);
      } catch (error) {
        console.error('Error fetching status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="dashboard loading">Loading...</div>;
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