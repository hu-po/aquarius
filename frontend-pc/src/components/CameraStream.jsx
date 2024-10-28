import React, { useEffect, useRef } from 'react';

const CameraStream = ({ deviceIndex }) => {
  const imgRef = useRef(null);
  const wsRef = useRef(null);
  const [error, setError] = useState(null);
  const [reconnecting, setReconnecting] = useState(false);

  useEffect(() => {
    let reconnectTimeout;
    const connectWebSocket = () => {
      const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      const wsUrl = BACKEND_URL.replace('http', 'ws');
      
      if (wsRef.current) {
        wsRef.current.close();
      }

      wsRef.current = new WebSocket(`${wsUrl}/ws/camera/${deviceIndex}`);
      
      wsRef.current.onmessage = (event) => {
        const reader = new FileReader();
        reader.onload = () => {
          if (imgRef.current) {
            imgRef.current.src = reader.result;
            setError(null);
          }
        };
        reader.readAsDataURL(event.data);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
      };

      wsRef.current.onclose = () => {
        setError('Connection closed');
        // Try to reconnect after 5 seconds
        if (!reconnecting) {
          setReconnecting(true);
          reconnectTimeout = setTimeout(() => {
            setReconnecting(false);
            connectWebSocket();
          }, 5000);
        }
      };
    };

    connectWebSocket();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deviceIndex]);

  return (
    <div className="camera-stream">
      {error && <div className="stream-error">{error}</div>}
      {reconnecting && <div className="stream-reconnecting">Reconnecting...</div>}
      <img
        ref={imgRef}
        className="stream-image"
        alt={`Camera ${deviceIndex} stream`}
      />
    </div>
  );
};

export default CameraStream;