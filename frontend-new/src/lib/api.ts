import axios from 'axios';

// Default to backend port 8000
const API_BASE_URL = '/api/v1';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add API key to all requests
api.interceptors.request.use(
    (config) => {
        // Get API key from localStorage
        if (typeof window !== 'undefined') {
            const apiKey = localStorage.getItem('api_key');
            if (apiKey) {
                config.headers.Authorization = `Bearer ${apiKey}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for better error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle 401 Unauthorized - redirect to login
        if (error.response?.status === 401) {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('api_key');
                localStorage.removeItem('user');
                // Only redirect if not already on login page
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login';
                }
            }
        }

        // Determine error message
        const message = error.response?.data?.detail || error.message || 'Something went wrong';
        console.error('API Error:', message);
        return Promise.reject({ ...error, message });
    }
);
