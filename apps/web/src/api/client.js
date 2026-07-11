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
    return { error: "Couldn't reach the analysis API. Please try again later." };
  }
};
