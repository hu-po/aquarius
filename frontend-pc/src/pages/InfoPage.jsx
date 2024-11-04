import React from 'react';
import { Life, Stats } from '../components';

export const InfoPage = () => {
  return (
    <div className="info-page">
      <div className="info-grid">
        <div className="stats-section">
          <h2>Temperature</h2>
          <Stats />
        </div>
        <div className="life-section">
          <h2>Life</h2>
          <Life />
        </div>
      </div>
    </div>
  );
};

export default InfoPage; 