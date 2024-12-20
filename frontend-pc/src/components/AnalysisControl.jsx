import React, { useState } from 'react';
import { Analyze } from '../services/api';

const AI_MODELS = [
  { id: 'claude', label: '🔮 claude' },
  { id: 'gpt', label: '🤖 gpt' },
  { id: 'gemini', label: '🌟 gemini' }
];

const ANALYSES = [
  { id: 'identify_life', label: '🐠 find life' },
  { id: 'estimate_temperature', label: '🌡️ get temp' }
];

const AnalysisControl = ({ onAnalysisComplete }) => {
  const [selectedModels, setSelectedModels] = useState(new Set(['claude', 'gpt', 'gemini']));
  const [selectedAnalyses, setSelectedAnalyses] = useState(new Set(['identify_life']));
  const [loading, setLoading] = useState(false);

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => {
      const next = new Set(prev);
      if (next.has(modelId)) next.delete(modelId);
      else next.add(modelId);
      return next;
    });
  };

  const handleAnalysisToggle = (analysisId) => {
    setSelectedAnalyses(prev => {
      const next = new Set(prev);
      if (next.has(analysisId)) next.delete(analysisId);
      else next.add(analysisId);
      return next;
    });
  };

  const handleAnalyze = async () => {
    if (selectedModels.size === 0 || selectedAnalyses.size === 0) return;
    setLoading(true);
    try {
      const modelString = Array.from(selectedModels).join(',');
      const analysisString = Array.from(selectedAnalyses).join(',');
      const results = await Analyze(modelString, analysisString);
      onAnalysisComplete(results);
    } catch (error) {
      console.error('Analysis failed:', error);
      onAnalysisComplete({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="controls-section">
      <div className="options-grid">
        <div className="options-column">
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
        <div className="options-column">
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
      </div>
      <button
        className={`analyze-button ${loading ? 'analyzing' : ''}`}
        onClick={handleAnalyze}
        disabled={loading || selectedModels.size === 0 || selectedAnalyses.size === 0}
      >
        {loading ? '🧠 ... ⏳' : '🧠 Analyze'}
      </button>
    </div>
  );
};

export default AnalysisControl;
