import axios from 'axios';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = import.meta.env.API_TIMEOUT || 10000;
const CAPTURE_TIMEOUT = import.meta.env.CAPTURE_TIMEOUT || 30000;
const ANALYSIS_TIMEOUT = import.meta.env.ANALYSIS_TIMEOUT || 60000;
const STREAM_RESUME_TIMEOUT = import.meta.env.STREAM_RESUME_TIMEOUT || 200;

const api = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Accept': 'application/json'
  }
});

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
    // Wait briefly to ensure stream is stopped
    await new Promise(resolve => setTimeout(resolve, STREAM_RESUME_TIMEOUT));
    
    const response = await api.post(`/capture/${deviceIndex}`, null, {
      timeout: CAPTURE_TIMEOUT
    });
    
    // Wait briefly before resuming stream
    await new Promise(resolve => setTimeout(resolve, STREAM_RESUME_TIMEOUT));
    
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error(`Camera ${deviceIndex} not found`);
    }
    if (error.response?.status === 400) {
      throw new Error(`Camera ${deviceIndex} is not active`);
    }
    if (error.response?.status === 500) {
      throw new Error(`Failed to capture from camera ${deviceIndex}: ${error.response?.data?.detail || ''}`);
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

export const Analyze = async (models, analyses) => {
  try {
    const encodedModels = encodeURIComponent(models);
    const encodedAnalyses = encodeURIComponent(analyses);
    
    const response = await api.post(`/analyze/${encodedModels}/${encodedAnalyses}`, null, {
      timeout: ANALYSIS_TIMEOUT
    });
    
    if (response.data.errors && Object.keys(response.data.errors).length > 0) {
      console.warn('Some analyses failed:', response.data.errors);
    }
    
    return {
      analysis: response.data.analysis || {},
      errors: response.data.errors || {}
    };
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error('No images available for analysis');
    }
    if (error.response?.status === 400) {
      throw new Error(error.response.data.detail || 'Invalid analysis request');
    }
    handleApiError(error, 'Failed to analyze image');
  }
};

export const sendRobotCommand = async (commandData) => {
  try {
    const response = await api.post('/robot/command', commandData);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to send robot command');
  }
};

export const getTrajectories = async () => {
  try {
    const response = await api.get('/robot/trajectories');
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to fetch trajectories');
  }
};

export const saveTrajectory = async (name) => {
  try {
    const response = await api.post(`/robot/trajectories/${name}`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to save trajectory');
  }
};

export const deleteTrajectory = async (name) => {
  try {
    const response = await api.delete(`/robot/trajectories/${name}`);
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to delete trajectory');
  }
};

export const toggleScan = async (enabled) => {
  try {
    const response = await api.post('/robot/scan/toggle', { enabled });
    return response.data;
  } catch (error) {
    handleApiError(error, 'Failed to toggle scan');
  }
};

export const getAnalysisHistory = async (limit = 10) => {
  const response = await axios.get(`${BASE_URL}/analyses?limit=${limit}`);
  return response.data;
};
