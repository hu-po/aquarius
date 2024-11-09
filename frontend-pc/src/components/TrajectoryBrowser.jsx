import React, { useState, useEffect, useCallback } from 'react';
import { getTrajectories, loadTrajectory, saveTrajectory } from '../services/api';

const TrajectoryBrowser = () => {
  const [trajectories, setTrajectories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTrajectory, setSelectedTrajectory] = useState(null);
  const [newName, setNewName] = useState('');
  const [saving, setSaving] = useState(false);

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

  const handleLoad = async (name) => {
    try {
      setLoading(true);
      setSelectedTrajectory(name);
      await loadTrajectory(name);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
        >
          {saving ? '💾 ...' : '💾 Save'}
        </button>
      </div>

      <div className="trajectories-list">
        {trajectories?.length > 0 ? (
          trajectories.map(traj => (
            <div 
              key={traj.name}
              className={`trajectory-item ${selectedTrajectory === traj.name ? 'selected' : ''}`}
              onClick={() => handleLoad(traj.name)}
            >
              <div className="trajectory-name">{traj.name}</div>
            </div>
          ))
        ) : (
          <div className="no-trajectories">No trajectories available</div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default TrajectoryBrowser; 