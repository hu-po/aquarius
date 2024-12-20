import React, { useState, useEffect, useCallback, useRef, forwardRef } from 'react';
import { getTrajectories, saveTrajectory, deleteTrajectory, sendRobotCommand } from '../services/api';

const TrajectoryBrowser = forwardRef((props, ref) => {
  const [trajectories, setTrajectories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTrajectories, setSelectedTrajectories] = useState(new Set());
  const [newName, setNewName] = useState('');
  const [saving, setSaving] = useState(false);
  const [playing, setPlaying] = useState(false);
  const inputRef = useRef(null);
  const prevTrajectoriesRef = useRef([]);

  const TRAJECTORY_FETCH_INTERVAL = import.meta.env.VITE_TRAJECTORY_FETCH_INTERVAL || 30000;

  const fetchTrajectories = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getTrajectories();
      setTrajectories(data?.trajectories || []);
      
      // Auto-select newly added trajectories
      const currentNames = new Set(prevTrajectoriesRef.current.map(t => t.name));
      const newTrajectories = (data?.trajectories || []).filter(t => !currentNames.has(t.name));
      if (newTrajectories.length > 0) {
        setSelectedTrajectories(prev => {
          const next = new Set(prev);
          newTrajectories.forEach(t => next.add(t.name));
          return next;
        });
      }
      
      prevTrajectoriesRef.current = data?.trajectories || [];
      setError(null);
    } catch (err) {
      setError(err.message);
      setTrajectories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrajectories();
    const interval = setInterval(fetchTrajectories, TRAJECTORY_FETCH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchTrajectories, TRAJECTORY_FETCH_INTERVAL]);

  const handleToggleSelect = (name) => {
    setSelectedTrajectories(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const handleSave = async () => {
    if (!newName.trim()) return;
    try {
      setSaving(true);
      await saveTrajectory(newName.trim());
      setNewName('');
      await fetchTrajectories();
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (selectedTrajectories.size === 0) return;
    try {
      setLoading(true);
      for (const name of selectedTrajectories) {
        await deleteTrajectory(name);
      }
      setSelectedTrajectories(new Set());
      await fetchTrajectories();
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = async () => {
    if (selectedTrajectories.size === 0) return;
    try {
      setPlaying(true);
      await sendRobotCommand({
        command: 'P',
        trajectory_name: JSON.stringify(Array.from(selectedTrajectories))
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setPlaying(false);
    }
  };

  const focusInput = () => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && newName.trim()) {
      handleSave();
    }
  };

  // Expose focusInput method via ref
  React.useImperativeHandle(ref, () => ({
    focusInput
  }));

  if (loading) return <div className="loading">Loading trajectories...</div>;

  return (
    <div className="trajectories-browser">
      <div className="trajectory-controls">
        <input
          ref={inputRef}
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="{tank}{text_description}"
          disabled={saving}
        />
        <button 
          onClick={handleSave}
          disabled={!newName.trim() || saving}
          className="save-button"
        >
          {saving ? '💾 ...' : '💾 Save'}
        </button>
      </div>

      <div className="trajectories-table">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Name</th>
              <th>Modified</th>
            </tr>
          </thead>
          <tbody>
            {trajectories?.length > 0 ? (
              trajectories.map(traj => (
                <tr key={traj.name}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedTrajectories.has(traj.name)}
                      onChange={() => handleToggleSelect(traj.name)}
                    />
                  </td>
                  <td>{traj.name}</td>
                  <td>{traj.modified}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={3}>No trajectories available</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="trajectory-actions">
        <button
          onClick={handlePlay}
          disabled={selectedTrajectories.size === 0 || playing}
          className="play-button"
        >
          {playing ? '▶️ playing...' : '▶️ play'}
        </button>
        <button
          onClick={handleDelete}
          disabled={selectedTrajectories.size === 0 || loading}
          className="delete-button"
        >
          🗑️ delete
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
});

export default TrajectoryBrowser; 