import React, { useState, useEffect } from 'react';
import { Analyze } from '../services/api';
import axios from 'axios';

const AI_MODELS = [
  { id: 'claude', label: '🧠 claude' },
  { id: 'gpt', label: '🤖 gpt' },
  { id: 'gemini', label: '🌟 gemini' }
];

const ANALYSES = [
  { id: 'identify_life', label: '🐠 Identify Life' },
  { id: 'estimate_temperature', label: '🌡️ Estimate Temperature' }
];

const AIAnalysis = () => {
  const [selectedModels, setSelectedModels] = useState(new Set(['claude']));
  const [selectedAnalyses, setSelectedAnalyses] = useState(new Set(['identify_life']));
  const [loading, setLoading] = useState(false);
  const [latestImage, setLatestImage] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  const FETCH_INTERVAL = import.meta.env.IMAGE_FETCH_INTERVAL || 30000;

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => {
      const next = new Set(prev);
      if (next.has(modelId)) {
        next.delete(modelId);
      } else {
        next.add(modelId);
      }
      return next;
    });
  };

  const handleAnalysisToggle = (analysisId) => {
    setSelectedAnalyses(prev => {
      const next = new Set(prev);
      if (next.has(analysisId)) {
        next.delete(analysisId);
      } else {
        next.add(analysisId);
      }
      return next;
    });
  };

  const fetchLatestImage = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/images?limit=1`);
      setLatestImage(response.data[0]);
      setImageLoading(false);
    } catch (error) {
      console.error('Failed to fetch image:', error);
      setImageLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestImage();
    const interval = setInterval(fetchLatestImage, FETCH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${BACKEND_URL}/images/${filename}`;
  };

  const handleAnalyze = async () => {
    if (selectedModels.size === 0 || selectedAnalyses.size === 0) return;
    setLoading(true);
    try {
      const modelString = Array.from(selectedModels).join(',');
      const analysisString = Array.from(selectedAnalyses).join(',');
      await Analyze(modelString, analysisString);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-container">
      <div className="analysis-grid">
        <div className="latest-image">
          {imageLoading ? (
            <div>Loading image...</div>
          ) : !latestImage ? (
            <div>No images available</div>
          ) : !imageError ? (
            <img 
              src={getImageUrl(latestImage?.filepath)}
              alt="Latest aquarium capture"
              className="aquarium-image"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="image-error">Failed to load image</div>
          )}
        </div>

        <div className="controls-section">
          <div className="model-toggles">
            {AI_MODELS.map(model => (
              <label key={model.id} className="toggle-label">
                <input
                  type="checkbox"
                  checked={selectedModels.has(model.id)}
                  onChange={() => handleModelToggle(model.id)}
                />
                {model.label}
              </label>
            ))}
          </div>

          <div className="analysis-toggles">
            {ANALYSES.map(analysis => (
              <label key={analysis.id} className="toggle-label">
                <input
                  type="checkbox"
                  checked={selectedAnalyses.has(analysis.id)}
                  onChange={() => handleAnalysisToggle(analysis.id)}
                />
                {analysis.label}
              </label>
            ))}
          </div>

          <button
            className={`analyze-button ${loading ? 'analyzing' : ''}`}
            onClick={handleAnalyze}
            disabled={loading || selectedModels.size === 0 || selectedAnalyses.size === 0}
          >
            {loading ? '🧠 Analyzing...' : '🧠 Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIAnalysis;
