import React from 'react';

const AIAnalysis = ({ responses }) => {
  if (!responses || Object.keys(responses).length === 0) {
    return <div className="model-response">no model responses available</div>;
  }

  return (
    <div className="model-response">
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
  );
};

export default AIAnalysis;
