import React from 'react';
import './LatestImage.css';

const LatestImage = ({ image }) => {
  if (!image) {
    return <div className="latest-image">No image available</div>;
  }

  return (
    <div className="latest-image">
      <h2>Latest Image</h2>
      <img 
        src={`http://localhost:8000/images/${image.filepath.split('/').pop()}`}
        alt="Latest aquarium capture"
        className="aquarium-image"
      />
      <div className="image-info">
        <div>Resolution: {image.width} x {image.height}</div>
        <div>Captured: {new Date(image.timestamp).toLocaleString()}</div>
      </div>
    </div>
  );
};

const getSecureImagePath = (filepath) => {
  const filename = filepath.split('/').pop(); // Get just filename
  return encodeURIComponent(filename); // URL encode for safety
};

export default LatestImage;