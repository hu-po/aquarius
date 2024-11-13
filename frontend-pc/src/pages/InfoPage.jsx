import React from 'react';
import { LifeTable, TemperaturePlot, ConfigViewer } from '../components';

export const InfoPage = () => {
  return (
    <div className="info-page">
      <div className="info-grid">
        <div className="temperature-section">
          <TemperaturePlot />
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