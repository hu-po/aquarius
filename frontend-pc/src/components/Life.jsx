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

  const categories = ['fish', 'plant', 'invertebrate'];

  return (
    <div className="life-table">
      {categories.map(category => (
        <div key={category} className="life-category">
          <h3>{category.charAt(0).toUpperCase() + category.slice(1)}s</h3>
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Name</th>
                <th>Count</th>
                <th>Introduced</th>
                <th>Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {life
                .filter(l => l.category === category)
                .map(l => (
                  <tr key={l.id}>
                    <td>{l.emoji}</td>
                    <td>
                      <div>{l.common_name}</div>
                      <div className="scientific-name">{l.scientific_name}</div>
                    </td>
                    <td>{l.count}</td>
                    <td>{new Date(l.introduced_at).toLocaleDateString()}</td>
                    <td>{new Date(l.last_seen_at).toLocaleDateString()}</td>
                  </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
};

export default Life; 