import React, { useEffect, useRef } from 'react';

const CameraStream = ({ deviceIndex }) => {
  const imgRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    const wsUrl = BACKEND_URL.replace('http', 'ws');
    
    wsRef.current = new WebSocket(`${wsUrl}/ws/camera/${deviceIndex}`);
    
    wsRef.current.onmessage = (event) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (imgRef.current) {
          imgRef.current.src = reader.result;
        }
      };
      reader.readAsDataURL(event.data);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deviceIndex]);

  return (
    <div className="camera-stream">
      <img
        ref={imgRef}
        className="stream-image"
        alt={`Camera ${deviceIndex} stream`}
      />
    </div>
  );
};

export default CameraStream;