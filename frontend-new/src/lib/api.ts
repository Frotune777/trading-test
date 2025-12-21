import axios from 'axios';

// Default to backend port 8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for better error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Determine error message
        const message = error.response?.data?.detail || error.message || 'Something went wrong';
        console.error('API Error:', message);
        return Promise.reject({ ...error, message });
    }
);
