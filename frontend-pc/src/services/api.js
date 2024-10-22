import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    throw new Error(`Server error: ${error.response.data.detail || 'Unknown error'}`);
  } else if (error.request) {
    // Request made but no response
    throw new Error('No response from server. Please check your connection.');
  } else {
    // Error in request setup
    throw new Error(`Request failed: ${error.message}`);
  }
};

export const getStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/status`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

export const getImages = async (limit = 10, offset = 0) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/images?limit=${limit}&offset=${offset}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

export const getReadingsHistory = async (hours = 24) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/readings/history?hours=${hours}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};