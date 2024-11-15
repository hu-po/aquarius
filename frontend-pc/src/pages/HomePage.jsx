import React from 'react';
import AnalysisHistory from '../components/AnalysisHistory';
import ToggleScan from '../components/ToggleScan';

export const HomePage = () => {
  return (
    <div className="home-page" style={{ msOverflowStyle: 'none', scrollbarWidth: 'none' }}>
      <div className="home-content">
        <div className="scan-control">
          <ToggleScan />
        </div>
        <AnalysisHistory />
      </div>
      <style>{`
        .home-page::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
};

export default HomePage;
