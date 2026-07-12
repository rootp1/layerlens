import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';

export const analyzePost = async (imageName, dockerFile) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/analyze`, {
      image_name: imageName,
      dockerfile: dockerFile,
    });
    return response.data;
  } catch (error) {
    console.error('There was an error sending the data to the API', error);
    // Axios throws on non-2xx responses — the backend still sends a specific
    // { error: "..." } body for rejected/failed scans (bad image name, dive
    // failure, etc.), so surface that instead of a generic message.
    const backendMessage = error?.response?.data?.error;
    return { error: backendMessage || "Couldn't reach the analysis API. Please try again later." };
  }
};

export const lintPost = async (dockerFile) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/lint`, {
      dockerfile: dockerFile,
    });
    return response.data;
  } catch (error) {
    console.error('There was an error linting the Dockerfile', error);
    const backendMessage = error?.response?.data?.error;
    return { error: backendMessage || "Couldn't reach the lint API. Please try again later." };
  }
};
