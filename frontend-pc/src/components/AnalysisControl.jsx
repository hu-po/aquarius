import React, { useState, useEffect } from 'react';
import { Analyze, getStatus, toggleScan } from '../services/api';

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
  const [scanEnabled, setScanEnabled] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const statusData = await getStatus();
        setScanEnabled(statusData?.scan_enabled || false);
      } catch (err) {
        console.error('Failed to load status:', err);
      }
    };

    loadStatus();
    const statusInterval = setInterval(loadStatus, 30000);
    return () => clearInterval(statusInterval);
  }, []);

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

  const handleToggleScan = async () => {
    setScanLoading(true);
    try {
      await toggleScan(!scanEnabled);
      setScanEnabled(!scanEnabled);
    } catch (err) {
      console.error('Failed to toggle scan:', err);
    } finally {
      setScanLoading(false);
    }
  };

  return (
    <div className="controls-section">
      <div className="controls-layout">
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
      </div>

      <div className="controls-buttons">
        <button
          className={`analyze-button ${loading ? 'analyzing' : ''}`}
          onClick={handleAnalyze}
          disabled={loading || selectedModels.size === 0 || selectedAnalyses.size === 0}
        >
          {loading ? '🧠 ... ⏳' : '🧠'}
        </button>

        <button
          onClick={handleToggleScan}
          disabled={scanLoading}
          className={`scan-toggle ${scanEnabled ? 'active' : ''}`}
          title={`Scheduled scan is ${scanEnabled ? 'enabled' : 'disabled'}`}
        >
          {scanLoading ? '⏳' : scanEnabled ? '🔍 Auto Scan On' : '⏹️ Auto Scan Off'}
        </button>
      </div>
    </div>
  );
};

export default AnalysisControl;
