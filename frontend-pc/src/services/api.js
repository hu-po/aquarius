import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL
});

export const getStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch data');
  }
};

export const getDevices = async () => {
  try {
    const response = await api.get('/devices');
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch devices');
  }
};

export const captureImage = async (deviceIndex = 0) => {
  try {
    const response = await api.post(`/capture/${deviceIndex}`);
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to capture image');
  }
};