import React from 'react';
import AnalysisHistory from '../components/AnalysisHistory';

export const HomePage = () => {
  return (
    <div className="home-page">
      <div className="home-content">
        <AnalysisHistory />
      </div>
    </div>
  );
};

export default HomePage;
