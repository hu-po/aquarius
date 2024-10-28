import React from 'react';
import PropTypes from 'prop-types';

const CameraStream = ({ deviceIndex }) => {
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  
  return (
    <div className="camera-stream">
      <img
        src={`${BACKEND_URL}/camera/${deviceIndex}/stream`}
        alt={`Camera ${deviceIndex} stream`}
        className="stream-image"
      />
    </div>
  );
};

CameraStream.propTypes = {
  deviceIndex: PropTypes.number.isRequired
};

export default CameraStream;
