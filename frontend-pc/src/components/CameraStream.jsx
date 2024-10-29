import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { getStreamUrl } from '../services/api';

const CameraStream = ({ deviceIndex, isPaused }) => {
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const imgRef = useRef(null);
  
  useEffect(() => {
    if (isPaused) {
      return; // Don't setup stream if paused
    }

    const maxRetries = 3;
    const retryDelay = 2000;
    
    const setupStream = () => {
      if (imgRef.current) {
        imgRef.current.onerror = () => {
          setError('Stream connection failed');
          if (retryCount < maxRetries) {
            setTimeout(() => {
              setRetryCount(prev => prev + 1);
              if (imgRef.current && !isPaused) {
                imgRef.current.src = `${getStreamUrl(deviceIndex)}?t=${Date.now()}`;
              }
            }, retryDelay);
          }
        };
        
        imgRef.current.onload = () => {
          setError(null);
          setRetryCount(0);
        };
      }
    };
    
    setupStream();
    
    return () => {
      if (imgRef.current) {
        imgRef.current.onerror = null;
        imgRef.current.onload = null;
      }
    };
  }, [deviceIndex, retryCount, isPaused]);

  return (
    <div className="camera-stream">
      {isPaused ? (
        <div className="stream-paused">Capturing image...</div>
      ) : error && retryCount >= 3 ? (
        <div className="stream-error">Stream unavailable: {error}</div>
      ) : (
        <img
          ref={imgRef}
          src={getStreamUrl(deviceIndex)}
          alt={`Camera ${deviceIndex} stream`}
          className="stream-image"
        />
      )}
      {!isPaused && error && retryCount < 3 && (
        <div className="stream-reconnecting">
          Reconnecting... ({retryCount + 1}/3)
        </div>
      )}
    </div>
  );
};

CameraStream.propTypes = {
  deviceIndex: PropTypes.number.isRequired,
  isPaused: PropTypes.bool
};

export default CameraStream;
