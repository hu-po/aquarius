import React, { useState, useEffect } from 'react';

const ConfigViewer = () => {
  const [configs, setConfigs] = useState({});

  useEffect(() => {
    const fetchEnvFile = async () => {
      try {
        const response = await fetch('/.env');
        const text = await response.text();
        const envConfigs = text.split('\n').reduce((acc, line) => {
          const [key, value] = line.split('=').map(str => str.trim());
          if (key && value) acc[key] = value;
          return acc;
        }, {});
        setConfigs(envConfigs);
      } catch (error) {
        console.error('Failed to load .env file:', error);
      }
    };

    fetchEnvFile();
  }, []);

  return (
    <div className="config-debug">
      <h2>Config Variables</h2>
      <pre>
        {Object.entries(configs).map(([key, value]) => (
          `${key}: ${value}\n`
        ))}
      </pre>
    </div>
  );
};

export default ConfigViewer; 