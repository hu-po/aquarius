import React from 'react';
import AnalysisHistory from '../components/AnalysisHistory';
import ToggleScan from '../components/ToggleScan';

export const HomePage = () => {
  return (
    <div className="home-page">
      <div className="home-content">
        <div className="scan-control">
          <ToggleScan />
        </div>
        <AnalysisHistory />
      </div>
    </div>
  );
};

export default HomePage;
