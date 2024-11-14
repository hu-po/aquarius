import React, { useState } from 'react';
import { AnalysisControl } from '../components';
import AnalysisHistory from '../components/AnalysisHistory';

export const AnalysisPage = () => {
  const [analysisComplete, setAnalysisComplete] = useState(false);

  const handleAnalysisComplete = (results) => {
    setAnalysisComplete(true);
    setTimeout(() => setAnalysisComplete(false), 2000);
  };

  return (
    <div className="analysis-page">
      <div className="analysis-content">
        <AnalysisControl onAnalysisComplete={handleAnalysisComplete} />
      </div>
      <div className="analysis-history">
        <AnalysisHistory key={analysisComplete ? 'refresh' : 'normal'} />
      </div>
    </div>
  );
};

export default AnalysisPage; 