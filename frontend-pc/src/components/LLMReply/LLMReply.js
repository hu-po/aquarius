import React, { useState } from 'react';
import './LLMReply.css';

const LLMReply = ({ descriptions }) => {
  const [selectedModel, setSelectedModel] = useState(Object.keys(descriptions || {})[0]);

  if (!descriptions || Object.keys(descriptions).length === 0) {
    return <div className="llm-reply">No AI descriptions available</div>;
  }

  return (
    <div className="llm-reply">
      <h2>AI Analysis</h2>
      <div className="model-selector">
        {Object.keys(descriptions).map((model) => (
          <button
            key={model}
            className={`model-button ${selectedModel === model ? 'active' : ''}`}
            onClick={() => setSelectedModel(model)}
          >
            {model}
          </button>
        ))}
      </div>
      <div className="description">
        {descriptions[selectedModel]}
      </div>
    </div>
  );
};

export default LLMReply;