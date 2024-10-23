import axios from 'axios';
import { API } from '../config';

const handleApiError = (error) => {
  if (error.response) {
    throw new Error(`Server error: ${error.response.data.detail || 'Unknown error'}`);
  } else if (error.request) {
    throw new Error('No response from server. Please check your connection.');
  } else {
    throw new Error(`Request failed: ${error.message}`);
  }
};

export const getStatus = async () => {
  try {
    const response = await axios.get(`${API.BASE_URL}/status`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

export const captureImage = async (deviceId = 0) => {
  try {
    const response = await axios.post(`${API.BASE_URL}/capture`, null, {
      params: { device_id: deviceId }
    });
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

export const getImages = async (limit = 10, offset = 0) => {
  try {
    const response = await axios.get(`${API.BASE_URL}/images?limit=${limit}&offset=${offset}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

export const getReadingsHistory = async (hours = 24) => {
  try {
    const response = await axios.get(`${API.BASE_URL}/readings/history?hours=${hours}`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};