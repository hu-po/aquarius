import React, { useState, useEffect } from 'react';
import { getAnalysisHistory } from '../services/api';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const POLL_INTERVAL = import.meta.env.VITE_ANALYSIS_POLL_INTERVAL || 10000;
const CAMERA_IMG_TYPE = import.meta.env.VITE_CAMERA_IMG_TYPE || 'jpg';

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

const AnalysisHistory = () => {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalysisHistory = async () => {
      try {
        const data = await getAnalysisHistory();
        setHistory(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch analysis history:', err);
        setError(err.message);
      }
    };

    fetchAnalysisHistory();
    const interval = setInterval(fetchAnalysisHistory, POLL_INTERVAL);
    
    return () => clearInterval(interval);
  }, []);

  // Group analyses by image_id
  const groupedAnalyses = history.reduce((acc, item) => {
    if (!acc[item.image_id]) {
      acc[item.image_id] = {
        timestamp: item.timestamp,
        image_id: item.image_id,
        analyses: []
      };
    }
    acc[item.image_id].analyses.push(item);
    return acc;
  }, {});

  if (error) {
    return <div className="error-message">Error loading analysis history: {error}</div>;
  }

  return (
    <div className="analysis-history">
      {Object.values(groupedAnalyses).map((group) => (
        <div key={group.image_id} className="history-group">
          <div className="history-image">
            <img 
              src={`${BACKEND_URL}/images/${group.image_id}.${CAMERA_IMG_TYPE}`}
              alt={`Analysis from ${new Date(group.timestamp).toLocaleString()}`}
              className="history-thumbnail"
            />
            <div className="image-timestamp">
              {formatTimestamp(group.timestamp)}
              <span className="image-id">ID: {group.image_id}</span>
            </div>
          </div>
          <div className="history-results">
            {group.analyses.map((item) => (
              <div key={item.id} className="result-item">
                <h4>{item.ai_model} - {item.analysis}</h4>
                <pre>{item.response}</pre>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default AnalysisHistory;
