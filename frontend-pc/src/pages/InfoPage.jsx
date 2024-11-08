import React from 'react';
import { Life, Stats, ConfigViewer } from '../components';

export const InfoPage = () => {
  return (
    <div className="info-page">
      <div className="info-grid">
        <div className="stats-section">
          <h2>temperature</h2>
          <Stats />
        </div>
        <div className="life-section">
          <h2>life.csv</h2>
          <Life />
        </div>
        <div className="config-section">
          <h2>.env</h2>
          <ConfigViewer />
        </div>
      </div>
    </div>
  );
};

export default InfoPage; 