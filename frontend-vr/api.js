const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Error fetching status:', error);
        throw error;
    }
}

export async function getReadingsHistory(hours = 24) {
    try {
        const response = await fetch(`${API_BASE_URL}/readings/history?hours=${hours}`);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Error fetching readings history:', error);
        throw error;
    }
}

export function getImageUrl(filepath) {
    if (!filepath) return null;
    const filename = filepath.split('/').pop();
    if (!filename) return null;
    return `${API_BASE_URL}/images/${encodeURIComponent(filename)}`;
}

export const handleApiError = (error) => {
    const errorDiv = document.getElementById('loading');
    errorDiv.style.display = 'block';
    errorDiv.textContent = error.message || 'An error occurred';
    throw error;
  };