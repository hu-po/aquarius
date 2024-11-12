import React from 'react';
import { LifeTable, Stats, ConfigViewer } from '../components';

export const InfoPage = () => {
  return (
    <div className="info-page">
      <div className="info-grid">
        <div className="stats-section">
          <Stats />
        </div>
        <div className="life-section">
          <LifeTable />
        </div>
        <div className="config-section">
          <ConfigViewer />
        </div>
      </div>
    </div>
  );
};

export default InfoPage; 