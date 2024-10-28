import React from 'react';
import PropTypes from 'prop-types';
import { getStreamUrl } from '../services/api';

const CameraStream = ({ deviceIndex }) => {
  return (
    <div className="camera-stream">
      <img
        src={getStreamUrl(deviceIndex)}
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
