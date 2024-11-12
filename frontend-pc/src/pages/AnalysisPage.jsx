import React, { useState, useEffect } from 'react';
import { AIAnalysis } from '../components';
import AnalysisHistory from '../components/AnalysisHistory';
import { getAnalysisHistory } from '../services/api';

export const AnalysisPage = () => {
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [latestImage, setLatestImage] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  const fetchAnalysisHistory = async () => {
    try {
      const history = await getAnalysisHistory();
      setAnalysisHistory(history);
    } catch (error) {
      console.error('Failed to fetch analysis history:', error);
    }
  };

  useEffect(() => {
    fetchAnalysisHistory();
    const interval = setInterval(fetchAnalysisHistory, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNewAnalysis = async (image, results) => {
    await fetchAnalysisHistory();
  };

  return (
    <div className="analysis-page">
      <AIAnalysis 
        onAnalysisComplete={handleNewAnalysis}
        latestImage={latestImage}
        setLatestImage={setLatestImage}
        imageError={imageError}
        setImageError={setImageError}
        imageLoading={imageLoading}
        setImageLoading={setImageLoading}
      />
      <AnalysisHistory history={analysisHistory} />
    </div>
  );
};

export default AnalysisPage; 