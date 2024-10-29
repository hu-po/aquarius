import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000, // Add reasonable timeout
  headers: {
    'Accept': 'application/json'
  }
});

// Helper for consistent error handling
const handleApiError = (error, defaultMessage) => {
  console.error('API Error:', error);
  if (error.code === 'ERR_NETWORK') {
    throw new Error('backend not available 🐠');
  }
  if (error.response?.data?.detail) {
    throw new Error(error.response.data.detail);
  }
  throw new Error(defaultMessage);
};

export const getStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to fetch aquarium status');
  }
};

export const getDevices = async () => {
  try {
    const response = await api.get('/devices');
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to fetch camera devices');
  }
};

export const captureImage = async (deviceIndex) => {
  try {
    const response = await api.post(`/capture/${deviceIndex}`);
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error(`Camera ${deviceIndex} not found`);
    }
    if (error.response?.status === 400) {
      throw new Error(`Camera ${deviceIndex} is not active`);
    }
    if (error.response?.status === 500) {
      throw new Error(`Failed to capture from camera ${deviceIndex}`);
    }
    handleApiError(error, `Failed to capture image from camera ${deviceIndex}`);
  }
};

// Add helper for stream URL
export const getStreamUrl = (deviceIndex) => {
  return `${BASE_URL}/camera/${deviceIndex}/stream`;
};

export const getLife = async () => {
  try {
    const response = await api.get('/life');
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to fetch aquarium life');
  }
};

export const addLife = async (life) => {
  try {
    const response = await api.post('/life', life);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to add life');
  }
};

export const updateLife = async (id, life) => {
  try {
    const response = await api.put(`/life/${id}`, life);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to update life');
  }
};
