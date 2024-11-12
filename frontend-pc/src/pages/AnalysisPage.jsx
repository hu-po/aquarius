import React from 'react';
import { AnalysisControl } from '../components';
import AnalysisHistory from '../components/AnalysisHistory';

export const AnalysisPage = () => {
  return (
    <div className="analysis-page">
      <AnalysisControl />
      <AnalysisHistory />
    </div>
  );
};

export default AnalysisPage; 