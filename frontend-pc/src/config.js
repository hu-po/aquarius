export const API = {
    BASE_URL: process.env.BACKEND_URL,
    POLL_INTERVAL: Number(process.env.REACT_APP_POLL_INTERVAL),
  };
  
  export const DASHBOARD = {
    IMAGE_MAX_WIDTH: Number(process.env.REACT_APP_IMAGE_MAX_WIDTH),
    IMAGE_MAX_HEIGHT: Number(process.env.REACT_APP_IMAGE_MAX_HEIGHT),
  };
  
  export const STATS = {
    TEMP_WARNING_MIN: Number(process.env.REACT_APP_TEMP_WARNING_MIN),
    TEMP_WARNING_MAX: Number(process.env.REACT_APP_TEMP_WARNING_MAX),
    PH_WARNING_MIN: Number(process.env.REACT_APP_PH_WARNING_MIN),
    PH_WARNING_MAX: Number(process.env.REACT_APP_PH_WARNING_MAX),
    DECIMAL_PLACES: Number(process.env.REACT_APP_STAT_DECIMAL_PLACES),
  };