export const API = {
    BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    POLL_INTERVAL: Number(process.env.REACT_APP_POLL_INTERVAL || 30000),
  };
  
  export const DASHBOARD = {
    IMAGE_MAX_WIDTH: Number(process.env.REACT_APP_IMAGE_MAX_WIDTH || 1920),
    IMAGE_MAX_HEIGHT: Number(process.env.REACT_APP_IMAGE_MAX_HEIGHT || 1080),
  };
  
  export const STATS = {
    TEMP_WARNING_MIN: Number(process.env.REACT_APP_TEMP_WARNING_MIN || 74),
    TEMP_WARNING_MAX: Number(process.env.REACT_APP_TEMP_WARNING_MAX || 82),
    PH_WARNING_MIN: Number(process.env.REACT_APP_PH_WARNING_MIN || 6.5),
    PH_WARNING_MAX: Number(process.env.REACT_APP_PH_WARNING_MAX || 7.5),
    DECIMAL_PLACES: Number(process.env.REACT_APP_STAT_DECIMAL_PLACES || 1),
  };