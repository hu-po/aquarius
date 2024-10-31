import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Gallery = () => {
  const [latestImage, setLatestImage] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [loading, setLoading] = useState(true);
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  const FETCH_INTERVAL = import.meta.env.IMAGE_FETCH_INTERVAL || 30000;

  const fetchLatestImage = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/images?limit=1`);
      setLatestImage(response.data[0]);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch image:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestImage();
    const interval = setInterval(fetchLatestImage, FETCH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${BACKEND_URL}/images/${filename}`;
  };

  if (loading) return <div className="gallery">Loading images...</div>;
  if (!latestImage) return <div className="gallery">No images available</div>;

  return (
    <div className="gallery">
      <div className="carousel-container">
        {!imageError ? (
          <img 
            src={getImageUrl(latestImage?.filepath)}
            alt="Latest aquarium capture"
            className="aquarium-image"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="image-error">Failed to load image</div>
        )}
      </div>
    </div>
  );
};

export default Gallery; 