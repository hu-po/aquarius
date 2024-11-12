import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { getStreamUrl } from '../services/api';

const CameraStream = ({ deviceIndex, isPaused, onCapture }) => {
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const imgRef = useRef(null);
  
  const handleCapture = async () => {
    setIsCapturing(true);
    try {
      await onCapture(deviceIndex);
    } finally {
      setIsCapturing(false);
    }
  };
  
  useEffect(() => {
    if (isPaused) {
      if (imgRef.current) {
        imgRef.current.src = '';
        imgRef.current.onerror = null;
        imgRef.current.onload = null;
      }
      return;
    }

    const maxRetries = 5;
    const retryDelay = 1000;
    
    const setupStream = () => {
      if (imgRef.current) {
        imgRef.current.onerror = () => {
          setError('Stream connection failed');
          if (retryCount < maxRetries) {
            setTimeout(() => {
              setRetryCount(prev => prev + 1);
              if (imgRef.current && !isPaused) {
                const timestamp = Date.now();
                const streamUrl = `${getStreamUrl(deviceIndex)}?t=${timestamp}`;
                imgRef.current.src = streamUrl;
              }
            }, retryDelay);
          }
        };
        
        imgRef.current.onload = () => {
          setError(null);
          setRetryCount(0);
        };

        const timestamp = Date.now();
        const streamUrl = `${getStreamUrl(deviceIndex)}?t=${timestamp}`;
        imgRef.current.src = streamUrl;
      }
    };
    
    setupStream();
    
    return () => {
      if (imgRef.current) {
        imgRef.current.onerror = null;
        imgRef.current.onload = null;
        imgRef.current.src = '';
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
        <>
          <img
            ref={imgRef}
            src={getStreamUrl(deviceIndex)}
            alt={`Camera ${deviceIndex} stream`}
            className="stream-image"
          />
          <button 
            className={`capture-button ${isCapturing ? 'capturing' : ''}`}
            onClick={handleCapture}
            disabled={isCapturing || isPaused}
          >
            {isCapturing ? '📸 ...' : '📸'}
          </button>
        </>
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
  isPaused: PropTypes.bool,
  onCapture: PropTypes.func
};

export default CameraStream;
