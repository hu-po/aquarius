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

export const captureImage = async (deviceIndex = 0) => {
  try {
    const response = await api.post(`/capture/${deviceIndex}`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to capture image');
  }
};

// Helper to get stream URL (useful if needed elsewhere in the app)
export const getStreamUrl = (deviceIndex) => {
  return `${BASE_URL}/camera/${deviceIndex}/stream`;
};
