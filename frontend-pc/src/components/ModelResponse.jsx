import React from 'react';

const ModelResponse = ({ responses }) => {
  if (!responses || Object.keys(responses).length === 0) {
    return <div className="model-response">no model responses available</div>;
  }

  const modelIcons = {
    'claude': '🔮',
    'gpt4o-mini': '🤖',
    'gemini': '💫'
  };

  return (
    <div className="model-response">
      {Object.entries(responses).map(([model, response]) => (
        <div key={model} className="model-output">
          <div className="model-header">
            <span className="model-icon">{modelIcons[model] || '🔍'}</span>
            <span className="model-name">{model}</span>
          </div>
          <div className="response">
            {response}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ModelResponse;
