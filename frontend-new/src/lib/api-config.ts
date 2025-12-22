/**
 * API Configuration and Base URLs
 * Centralized configuration for backend API endpoints
 */

// Backend API base URL (adjust based on environment)
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // QUAD Reasoning Engine
  reasoning: (symbol: string) => `/api/v1/recommendations/${symbol}/reasoning`,
  
  // Legacy endpoints (existing)
  stockData: (symbol: string) => `/api/v1/stocks/${symbol}`,
  technicals: (symbol: string) => `/api/v1/technicals/${symbol}`,
  derivatives: (symbol: string) => `/api/v1/derivatives/${symbol}`,
  insider: (symbol: string) => `/api/v1/insider/${symbol}`,
} as const;

// Helper function to build full URL
export const buildApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};
