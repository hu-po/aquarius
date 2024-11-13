import React, { useState, useRef, useEffect } from 'react';
import { sendRobotCommand, captureImage } from '../services/api';
import { TrajectoryBrowser, CameraStream } from '../components';

const ROBOT_COMMANDS = [
  // Top row - movement controls
  { id: 'go-home', label: '🏠', description: 'Go Home', row: 'top' },
  { id: 'set-home', label: '📍', description: 'Set Home', row: 'top' },
  // Middle row - emergency
  { id: 'e-stop', label: '🔴', description: 'E-Stop', row: 'middle' },
  // Bottom row - recording
  { id: 'start-recording', label: '⏺️', description: 'Record', row: 'bottom' },
  { id: 'stop-recording', label: '⏹️', description: 'End Record', row: 'bottom' },
];

const SCAN_CAMERA_ID = parseInt(process.env.REACT_APP_SCAN_CAMERA_ID ?? 0);

const RobotPage = () => {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const trajectoryBrowserRef = useRef();
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    return () => {
      setIsPaused(true);
    };
  }, []);

  const handleCommand = async (command) => {
    setLoading(true);
    try {
      if (command === 'e-stop') {
        await sendRobotCommand({ command: 'f', trajectory_name: null });
      } else if (command === 'start-recording') {
        await sendRobotCommand({ command: 'r', trajectory_name: null });
      } else if (command === 'stop-recording') {
        await sendRobotCommand({ command: 'c', trajectory_name: null });
        // Focus input after stopping recording and going home
        setTimeout(() => trajectoryBrowserRef.current?.focusInput(), 100);
      } else if (command === 'go-home') {
        await sendRobotCommand({ command: 'h', trajectory_name: null });
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
      <div className="camera-container">
        <CameraStream
          deviceIndex={SCAN_CAMERA_ID}
          isPaused={isPaused}
        />
      </div>
      <div className="robot-grid">
        <div className="robot-row top">
          {ROBOT_COMMANDS.filter(cmd => cmd.row === 'top').map(cmd => (
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
        <div className="robot-row middle">
          {ROBOT_COMMANDS.filter(cmd => cmd.row === 'middle').map(cmd => (
            <button
              key={cmd.id}
              className={`robot-button emergency ${loading ? 'disabled' : ''}`}
              onClick={() => handleCommand(cmd.id)}
              disabled={loading}
              title={cmd.description}
            >
              <span className="emoji">{cmd.label}</span>
              <span className="description">{cmd.description}</span>
            </button>
          ))}
        </div>
        <div className="robot-row bottom">
          {ROBOT_COMMANDS.filter(cmd => cmd.row === 'bottom').map(cmd => (
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