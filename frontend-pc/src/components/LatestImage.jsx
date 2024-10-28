import React, { useState } from 'react';

const LatestImage = ({ image }) => {
  const [imageError, setImageError] = useState(false);
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  if (!image) {
    return <div className="latest-image">No image available</div>;
  }

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${BACKEND_URL}/images/${encodeURIComponent(filename)}`;
  };

  return (
    <div className="latest-image">
      {!imageError ? (
        <img 
          src={getImageUrl(image.filepath)}
          alt="Latest aquarium capture"
          className="aquarium-image"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="image-error">Failed to load image</div>
      )}
      <div className="image-info">
        <div>Captured: {new Date(image.timestamp).toLocaleString()}</div>
      </div>
    </div>
  );
};

export default LatestImage;
