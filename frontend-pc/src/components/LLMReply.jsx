import React from 'react';

const LLMReply = ({ descriptions }) => {
  if (!descriptions || Object.keys(descriptions).length === 0) {
    return <div className="llm-reply">No AI descriptions available</div>;
  }

  const modelIcons = {
    'claude': '🔮',
    'gpt4o-mini': '🤖',
    'gemini': '💫'
  };

  return (
    <div className="llm-reply">
      {Object.entries(descriptions).map(([model, description]) => (
        <div key={model} className="model-output">
          <div className="model-header">
            <span className="model-icon">{modelIcons[model] || '🔍'}</span>
            <span className="model-name">{model}</span>
          </div>
          <div className="description">
            {description}
          </div>
        </div>
      ))}
    </div>
  );
};

export default LLMReply;
