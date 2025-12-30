import { api } from '../api';

export interface User {
    id: number;
    username: string;
    email: string | null;
    is_active: boolean;
    is_superuser: boolean;
    order_mode: 'auto' | 'semi_auto';
    created_at: string;
    last_login: string | null;
}

export interface RegisterRequest {
    username: string;
    password: string;
    email?: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface APIKeyResponse {
    api_key: string;
    message: string;
}

export const authApi = {
    /**
     * Register a new user
     */
    register: async (data: RegisterRequest): Promise<User> => {
        const response = await api.post('/auth/register', data);
        return response.data;
    },

    /**
     * Login user with username and password
     */
    login: async (data: LoginRequest): Promise<User> => {
        const response = await api.post('/auth/login', data);
        return response.data;
    },

    /**
     * Generate a new API key for the current user
     * WARNING: This invalidates the previous API key!
     */
    generateApiKey: async (): Promise<APIKeyResponse> => {
        const response = await api.post('/auth/api-key/generate');
        return response.data;
    },

    /**
     * Revoke the current user's API key
     */
    revokeApiKey: async (): Promise<void> => {
        await api.delete('/auth/api-key/revoke');
    },

    /**
     * Get current authenticated user information
     */
    getCurrentUser: async (): Promise<User> => {
        const response = await api.get('/auth/me');
        return response.data;
    },

    /**
     * Update order execution mode
     * @param mode - 'auto' for immediate execution, 'semi_auto' for manual approval
     */
    updateOrderMode: async (mode: 'auto' | 'semi_auto'): Promise<User> => {
        const response = await api.put('/auth/order-mode', { mode });
        return response.data;
    },
};
