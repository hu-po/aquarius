import React, { useState } from 'react';
import { Analyze } from '../services/api';

const AI_MODELS = [
  { id: 'claude', label: '🧠 Claude' },
  { id: 'gpt', label: '🤖 GPT' },
  { id: 'gemini', label: '🌟 Gemini' }
];

const ANALYSES = [
  { id: 'identify_life', label: '🐠 Identify Life' },
  { id: 'estimate_temperature', label: '🌡️ Estimate Temperature' }
];

const AIAnalysis = ({ responses }) => {
  const [selectedModels, setSelectedModels] = useState(new Set(['claude']));
  const [selectedAnalyses, setSelectedAnalyses] = useState(new Set(['identify_life']));
  const [loading, setLoading] = useState(false);

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
    <div className="model-response">
      <div className="analysis-controls">
        <div className="checkbox-group">
          <div className="checkbox-section">
            <h3>Models</h3>
            {AI_MODELS.map(model => (
              <label key={model.id} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedModels.has(model.id)}
                  onChange={() => handleModelToggle(model.id)}
                />
                {model.label}
              </label>
            ))}
          </div>
          <div className="checkbox-section">
            <h3>Analyses</h3>
            {ANALYSES.map(analysis => (
              <label key={analysis.id} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedAnalyses.has(analysis.id)}
                  onChange={() => handleAnalysisToggle(analysis.id)}
                />
                {analysis.label}
              </label>
            ))}
          </div>
        </div>
        <button
          className={`capture-button ${loading ? 'capturing' : ''}`}
          onClick={handleAnalyze}
          disabled={loading || selectedModels.size === 0 || selectedAnalyses.size === 0}
        >
          {loading ? '🧠 Analyzing...' : '🧠 Analyze'}
        </button>
      </div>

      {responses && Object.keys(responses).length > 0 && (
        <div className="responses-grid">
          {Object.entries(responses).map(([model, response]) => (
            <div key={model} className="model-output">
              <div className="model-header">
                <span className="model-name">{model}</span>
              </div>
              <div className="response">
                {response}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIAnalysis;
