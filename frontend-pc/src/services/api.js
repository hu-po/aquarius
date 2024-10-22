import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getStatus = async () => {
  const response = await axios.get(`${API_BASE_URL}/status`);
  return response.data;
};

export const getImages = async (limit = 10, offset = 0) => {
  const response = await axios.get(`${API_BASE_URL}/images?limit=${limit}&offset=${offset}`);
  return response.data;
};

export const getReadingsHistory = async (hours = 24) => {
  const response = await axios.get(`${API_BASE_URL}/readings/history?hours=${hours}`);
  return response.data;
};