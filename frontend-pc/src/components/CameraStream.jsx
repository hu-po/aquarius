import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { getStreamUrl } from '../services/api';

const CameraStream = ({ deviceIndex, isPaused, onCapture }) => {
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const imgRef = useRef(null);
  const mountedRef = useRef(true);
  
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (imgRef.current) {
        imgRef.current.src = '';
        imgRef.current.onerror = null;
        imgRef.current.onload = null;
      }
      setError(null);
      setRetryCount(0);
    };
  }, []);
  
  const handleCapture = async () => {
    setIsCapturing(true);
    try {
      await onCapture(deviceIndex);
    } finally {
      if (mountedRef.current) {
        setIsCapturing(false);
      }
    }
  };
  
  useEffect(() => {
    if (!mountedRef.current) return;
    
    if (isPaused) {
      if (imgRef.current) {
        imgRef.current.src = '';
      }
      return;
    }

    const img = imgRef.current;
    if (!img) return;

    // Create a new URL with timestamp to prevent caching
    const streamUrl = `${getStreamUrl(deviceIndex)}?t=${Date.now()}`;
    img.src = streamUrl;

    const handleError = () => {
      if (!mountedRef.current) return;
      setError('Stream connection failed');
      if (retryCount < 3) {
        setTimeout(() => {
          if (mountedRef.current && !isPaused) {
            setRetryCount(prev => prev + 1);
            img.src = `${getStreamUrl(deviceIndex)}?t=${Date.now()}`;
          }
        }, 1000);
      }
    };

    const handleLoad = () => {
      if (!mountedRef.current) return;
      setError(null);
      setRetryCount(0);
    };

    img.addEventListener('error', handleError);
    img.addEventListener('load', handleLoad);

    return () => {
      img.removeEventListener('error', handleError);
      img.removeEventListener('load', handleLoad);
      img.src = '';
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
