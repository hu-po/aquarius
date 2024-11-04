import React, { useState, useEffect } from 'react';
import { Analyze } from '../services/api';
import axios from 'axios';

const AI_MODELS = [
  { id: 'claude', label: '🔮 claude' },
  { id: 'gpt', label: '🤖 gpt' },
  { id: 'gemini', label: '🌟 gemini' }
];

const ANALYSES = [
  { id: 'identify_life', label: '🐠 identify life' },
  { id: 'estimate_temperature', label: '🌡️ estimate temperature' }
];

const AIAnalysis = () => {
  const [selectedModels, setSelectedModels] = useState(new Set(['claude']));
  const [selectedAnalyses, setSelectedAnalyses] = useState(new Set(['identify_life']));
  const [loading, setLoading] = useState(false);
  const [latestImage, setLatestImage] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  const [analysisResults, setAnalysisResults] = useState(null);
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
    setAnalysisResults(null);
    try {
      const modelString = Array.from(selectedModels).join(',');
      const analysisString = Array.from(selectedAnalyses).join(',');
      const results = await Analyze(modelString, analysisString);
      setAnalysisResults(results);
    } catch (error) {
      console.error('Analysis failed:', error);
      setAnalysisResults({ error: error.message });
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
            <>
              <img 
                src={getImageUrl(latestImage?.filepath)}
                alt={`📷 cam${latestImage.device_index} • ${new Date(latestImage.timestamp).toLocaleString()}`}
                className="aquarium-image"
                onError={() => setImageError(true)}
              />
              <div className="image-info">
                📷 cam{latestImage.device_index} • {new Date(latestImage.timestamp).toLocaleString('en-US', { 
                  timeZone: status?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
                  dateStyle: 'medium',
                  timeStyle: 'medium'
                })}
              </div>
            </>
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
            {loading ? '🧠 ... ⏳' : '🧠'}
          </button>
        </div>
      </div>

      {analysisResults && (
        <div className="analysis-results">
          {analysisResults.error ? (
            <div className="error-message">{analysisResults.error}</div>
          ) : (
            <div className="results-grid">
              {Object.entries(analysisResults.analysis).map(([key, value]) => (
                <div key={key} className="result-item">
                  <h4>{key}</h4>
                  <pre>{value}</pre>
                </div>
              ))}
              {Object.keys(analysisResults.errors).length > 0 && (
                <div className="analysis-errors">
                  <h4>Errors</h4>
                  {Object.entries(analysisResults.errors).map(([key, error]) => (
                    <div key={key} className="error-item">
                      <strong>{key}:</strong> {error}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIAnalysis;
