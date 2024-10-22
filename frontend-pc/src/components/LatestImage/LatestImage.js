import React, { useState } from 'react';
import './LatestImage.css';

const LatestImage = ({ image }) => {
  const [imageError, setImageError] = useState(false);

  if (!image) {
    return (
      <div className="latest-image">
        <h2>Latest Image</h2>
        <div className="no-image-placeholder">No image available</div>
      </div>
    );
  }

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    return `${baseUrl}/images/${encodeURIComponent(filename)}`;
  };

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div className="latest-image">
      <h2>Latest Image</h2>
      {!imageError ? (
        <img 
          src={getImageUrl(image.filepath)}
          alt="Latest aquarium capture"
          className="aquarium-image"
          onError={handleImageError}
        />
      ) : (
        <div className="image-error">Failed to load image</div>
      )}
      <div className="image-info">
        <div>Resolution: {image.width} x {image.height}</div>
        <div>Captured: {new Date(image.timestamp).toLocaleString()}</div>
        <div>Device ID: {image.device_id}</div>
      </div>
    </div>
  );
};

export default LatestImage;