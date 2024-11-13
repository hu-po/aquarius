import React from 'react';
import { LifeTable, TemperaturePlot, LocationTime } from '../components';

export const InfoPage = () => {
  return (
    <div className="info-page">
      <div className="info-content">
        <LocationTime />
        <div className="temperature-section">
          <TemperaturePlot />
        </div>
        <div className="life-section">
          <LifeTable />
        </div>
      </div>
    </div>
  );
};

export default InfoPage; 