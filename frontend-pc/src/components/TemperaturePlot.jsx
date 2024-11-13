import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getReadingsHistory } from '../services/api';

const TANK_COLORS = {
  1: '#3b82f6', // blue
  2: '#10b981', // green
  3: '#6366f1'  // indigo
};

const TemperaturePlot = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await getReadingsHistory(24);
        setHistory(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load temperature history:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadHistory();
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading temperature data...</div>;
  if (error) return <div>Error: {error}</div>;

  const tankIds = [...new Set(history.map(r => r.tank_id))].sort();

  return (
    <div className="plot-container" style={{ height: '300px', background: '#1e293b', padding: '1rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
      <h3 style={{ margin: '0 0 1rem 0', color: '#e2e8f0', fontSize: '1.1rem' }}>Temperature History (24h)</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={history}>
          <XAxis 
            dataKey="timestamp" 
            type="number"
            domain={['auto', 'auto']}
            scale="time"
            tickFormatter={(timestamp) => new Date(timestamp).toLocaleTimeString()}
          />
          <YAxis 
            domain={['auto', 'auto']}
            label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
            formatter={(value, name) => [`${value.toFixed(1)}°F`, `Tank ${name}`]}
          />
          <Legend />
          {tankIds.map(tankId => (
            <Line
              key={tankId}
              type="monotone"
              dataKey="temperature_f"
              data={history.filter(r => r.tank_id === tankId)}
              name={`${tankId}`}
              stroke={TANK_COLORS[tankId]}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TemperaturePlot; 