import React, { useState, useEffect } from 'react';
import { getLife } from '../services/api';

const Life = () => {
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

  if (loading) return <div>Loading life data...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="life-table">
      <table>
        <thead>
          <tr>
            <th></th>
            <th>name</th>
            <th>num</th>
            <th>last seen</th>
          </tr>
        </thead>
        <tbody>
          {life.map(l => (
            <tr key={l.id}>
              <td>{l.emoji}</td>
              <td>{l.common_name}</td>
              <td>{l.count}</td>
              <td>{new Date(l.last_seen_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Life; 