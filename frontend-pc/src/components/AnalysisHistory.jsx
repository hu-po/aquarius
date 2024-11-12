import React from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const AnalysisHistory = ({ history }) => {
  return (
    <div className="analysis-history">
      {history.map((item) => (
        <div key={item.id} className="history-item">
          <div className="history-image">
            <img 
              src={`${BACKEND_URL}/images/${item.image_id}`}
              alt={`Analysis from ${new Date(item.timestamp).toLocaleString()}`}
              className="history-thumbnail"
            />
            <div className="image-timestamp">
              {new Date(item.timestamp).toLocaleString()}
            </div>
          </div>
          <div className="history-results">
            <div className="result-item">
              <h4>{item.ai_model} - {item.analysis}</h4>
              <pre>{item.response}</pre>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default AnalysisHistory;
