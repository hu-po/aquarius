import React, { useState } from 'react';
import { sendRobotCommand } from '../services/api';

const ROBOT_COMMANDS = [
  { id: 'f', label: '🔓', description: 'Release Robot' },
  { id: 'r', label: '⏺️', description: 'Start Record' },
  { id: 'c', label: '⏹️', description: 'Stop Record' },
  { id: 'p', label: '▶️', description: 'Play Once' },
  { id: 'P', label: '🔁', description: 'Loop Play/Stop' },
  { id: 'q', label: '🛑', description: 'Quit' }
];

const RobotPage = () => {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCommand = async (command) => {
    setLoading(true);
    try {
      const response = await sendRobotCommand(command);
      setStatus(`Success: ${response.message}`);
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="robot-page">
      <div className="robot-grid">
        {ROBOT_COMMANDS.map(cmd => (
          <button
            key={cmd.id}
            className={`robot-button ${loading ? 'disabled' : ''}`}
            onClick={() => handleCommand(cmd.id)}
            disabled={loading}
            title={cmd.description}
          >
            <span className="emoji">{cmd.label}</span>
            <span className="description">{cmd.description}</span>
          </button>
        ))}
      </div>
      {status && (
        <div className={`status-message ${status.includes('Error') ? 'error' : 'success'}`}>
          {status}
        </div>
      )}
    </div>
  );
};

export default RobotPage; 