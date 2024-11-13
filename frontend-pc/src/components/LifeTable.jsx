import React, { useState, useEffect } from 'react';
import { getLife } from '../services/api';

const LifeTable = () => {
  const [life, setLife] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadLife = async () => {
      try {
        const data = await getLife();
        setLife(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadLife();
    const interval = setInterval(loadLife, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatLastSeen = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  if (loading) return <div>Loading life data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="life-table">
      <table>
        <thead>
          <tr>
            <th className="text-center">emoji</th>
            <th className="text-center">name</th>
            <th className="text-center"><i>name</i></th>
            <th className="text-center">last seen</th>
            <th className="text-center">sightings</th>
          </tr>
        </thead>
        <tbody>
          {life.map(l => (
            <tr key={l.id}>
              <td className="text-center">{l.emoji}</td>
              <td className="text-center">{l.common_name}</td>
              <td className="text-center"><i>{l.scientific_name}</i></td>
              <td className="text-center">{formatLastSeen(l.last_seen_at)}</td>
              <td className="text-center">{l.image_refs.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LifeTable; 