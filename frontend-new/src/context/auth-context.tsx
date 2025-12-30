'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, authApi } from '@/lib/api/auth';

interface AuthContextType {
    user: User | null;
    apiKey: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, password: string, email?: string) => Promise<void>;
    logout: () => void;
    generateApiKey: () => Promise<string>;
    updateOrderMode: (mode: 'auto' | 'semi_auto') => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [apiKey, setApiKey] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Load from localStorage on mount
        const storedUser = localStorage.getItem('user');
        const storedKey = localStorage.getItem('api_key');

        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (error) {
                console.error('Failed to parse stored user:', error);
                localStorage.removeItem('user');
            }
        }

        if (storedKey) {
            setApiKey(storedKey);
        }

        setIsLoading(false);
    }, []);

    const login = async (username: string, password: string) => {
        try {
            // Login user
            const userData = await authApi.login({ username, password });
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));

            // Auto-generate API key after successful login
            const { api_key } = await authApi.generateApiKey();
            setApiKey(api_key);
            localStorage.setItem('api_key', api_key);
        } catch (error) {
            // Clear any partial state on error
            setUser(null);
            setApiKey(null);
            localStorage.removeItem('user');
            localStorage.removeItem('api_key');
            throw error;
        }
    };

    const register = async (username: string, password: string, email?: string) => {
        try {
            const userData = await authApi.register({ username, password, email });
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));

            // Auto-generate API key after registration
            const { api_key } = await authApi.generateApiKey();
            setApiKey(api_key);
            localStorage.setItem('api_key', api_key);
        } catch (error) {
            // Clear any partial state on error
            setUser(null);
            setApiKey(null);
            localStorage.removeItem('user');
            localStorage.removeItem('api_key');
            throw error;
        }
    };

    const logout = () => {
        setUser(null);
        setApiKey(null);
        localStorage.removeItem('user');
        localStorage.removeItem('api_key');
    };

    const generateApiKey = async (): Promise<string> => {
        const { api_key } = await authApi.generateApiKey();
        setApiKey(api_key);
        localStorage.setItem('api_key', api_key);
        return api_key;
    };

    const updateOrderMode = async (mode: 'auto' | 'semi_auto') => {
        const updatedUser = await authApi.updateOrderMode(mode);
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                apiKey,
                isAuthenticated: !!user && !!apiKey,
                isLoading,
                login,
                register,
                logout,
                generateApiKey,
                updateOrderMode,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
