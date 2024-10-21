export const fetchFishPositions = async () => {
    const response = await fetch('/api/fish');
    return await response.json();
};

export const fetchSystemStatus = async () => {
    const response = await fetch('/api/status');
    return await response.json();
};
