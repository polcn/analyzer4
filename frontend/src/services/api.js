import axios from 'axios';

// API base URL - will be set via environment variable in production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

export const analyzeFile = async (file, fileType) => {
  try {
    // Step 1: Get pre-signed upload URL
    const uploadResponse = await axios.post(`${API_BASE_URL}/upload`, {
      fileName: file.name,
      fileType: fileType
    });

    const { uploadUrl, analysisId, key } = uploadResponse.data;

    // Step 2: Upload file directly to S3
    await axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': 'text/csv'
      }
    });

    // Step 3: Trigger analysis
    await axios.post(`${API_BASE_URL}/analyze`, {
      bucket: process.env.REACT_APP_S3_BUCKET || 'sapanalyzer4-uploads',
      key: key,
      analysisId: analysisId,
      fileType: fileType
    });

    return { analysisId };

  } catch (error) {
    console.error('Error analyzing file:', error);
    throw new Error(error.response?.data?.error || 'Failed to analyze file');
  }
};

export const getResults = async (analysisId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/results/${analysisId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting results:', error);
    throw new Error(error.response?.data?.error || 'Failed to get results');
  }
};