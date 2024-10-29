import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Gallery = () => {
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageError, setImageError] = useState(false);
  const [loading, setLoading] = useState(true);
  const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  const IMAGES_TO_SHOW = 5;
  const AUTO_ADVANCE_INTERVAL = 5000;

  const fetchImages = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/images?limit=${IMAGES_TO_SHOW}`);
      setImages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch images:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
    const interval = setInterval(fetchImages, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const autoAdvance = setInterval(() => {
      if (images.length > 1) {
        setCurrentIndex(prev => (prev + 1) % images.length);
      }
    }, AUTO_ADVANCE_INTERVAL);
    return () => clearInterval(autoAdvance);
  }, [images.length]);

  const getImageUrl = (filepath) => {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    return `${BACKEND_URL}/images/${encodeURIComponent(filename)}`;
  };

  const handlePrevious = () => {
    setCurrentIndex(prev => (prev - 1 + images.length) % images.length);
  };

  const handleNext = () => {
    setCurrentIndex(prev => (prev + 1) % images.length);
  };

  if (loading) return <div className="gallery">Loading images...</div>;
  if (!images.length) return <div className="gallery">No images available</div>;

  return (
    <div className="gallery">
      <div className="carousel-container">
        {!imageError ? (
          <img 
            src={getImageUrl(images[currentIndex]?.filepath)}
            alt={`Aquarium capture ${currentIndex + 1}`}
            className="aquarium-image"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="image-error">Failed to load image</div>
        )}
      </div>
    </div>
  );
};

export default Gallery; 