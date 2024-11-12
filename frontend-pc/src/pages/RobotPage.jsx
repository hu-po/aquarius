import React, { useState, useRef } from 'react';
import { sendRobotCommand } from '../services/api';
import { TrajectoryBrowser } from '../components';

const ROBOT_COMMANDS = [
  { id: 'go-home', label: '🏠', description: 'Go Home' },
  { id: 'set-home', label: '📍', description: 'Set Home' },
  { id: 'release', label: '🔓', description: 'Release' },
  { id: 'start-recording', label: '⏺️', description: 'Record' },
  { id: 'stop-recording', label: '⏹️', description: 'End Record' },
];

const RobotPage = () => {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const trajectoryBrowserRef = useRef();

  const handleCommand = async (command) => {
    setLoading(true);
    try {
      if (command === 'release') {
        // Release robot before recording
        await sendRobotCommand({ command: 'f', trajectory_name: null });
        await sendRobotCommand({ command: 'r', trajectory_name: null });
      } else if (command === 'stop-recording') {
        await sendRobotCommand({ command: 'c', trajectory_name: null });
        // Go home after stopping recording
        await sendRobotCommand({ command: 'h', trajectory_name: null });
        // Focus input after stopping recording and going home
        setTimeout(() => trajectoryBrowserRef.current?.focusInput(), 100);
      } else if (command === 'go-home') {
        await sendRobotCommand({ command: 'h', trajectory_name: null });
        // Release robot after going home
        await sendRobotCommand({ command: 'f', trajectory_name: null });
      } else if (command === 'set-home') {
        await sendRobotCommand({ command: 'H', trajectory_name: null });
      } else {
        setStatus(`Error: Unknown robot command ${command}`);
      }
      setStatus(`Success: Command executed`);
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
      <TrajectoryBrowser ref={trajectoryBrowserRef} />
      {status && (
        <div className={`status-message ${status.includes('Error') ? 'error' : 'success'}`}>
          {status}
        </div>
      )}
    </div>
  );
};

export default RobotPage; 