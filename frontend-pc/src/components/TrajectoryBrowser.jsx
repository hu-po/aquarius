import React, { useState, useEffect, useCallback } from 'react';
import { getTrajectories, loadTrajectory, saveTrajectory, deleteTrajectory, sendRobotCommand } from '../services/api';

const TrajectoryBrowser = () => {
  const [trajectories, setTrajectories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTrajectories, setSelectedTrajectories] = useState(new Set());
  const [newName, setNewName] = useState('');
  const [saving, setSaving] = useState(false);
  const [playing, setPlaying] = useState(false);

  const fetchTrajectories = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getTrajectories();
      setTrajectories(data?.trajectories || []);
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
    const interval = setInterval(fetchTrajectories, 5000);
    return () => clearInterval(interval);
  }, [fetchTrajectories]);

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

  const handleLoopPlay = async () => {
    if (selectedTrajectories.size === 0) return;
    try {
      setPlaying(true);
      const trajectoryNames = Array.from(selectedTrajectories);
      await api.post('/robot/trajectories/play', { names: trajectoryNames });
    } catch (err) {
      setError(err.message);
    } finally {
      setPlaying(false);
    }
  };

  if (loading) return <div className="loading">Loading trajectories...</div>;

  return (
    <div className="trajectories-browser">
      <div className="save-trajectory">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="New trajectory name"
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

      <div className="trajectory-controls">
        <button
          onClick={handleLoopPlay}
          disabled={selectedTrajectories.size === 0 || playing}
          className="loop-button"
        >
          {playing ? '🔄 Playing...' : '🔄 Loop Selected'}
        </button>
        <button
          onClick={handleDelete}
          disabled={selectedTrajectories.size === 0 || loading}
          className="delete-button"
        >
          🗑️ Delete Selected
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

      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default TrajectoryBrowser; 