/**
 * API Configuration and Base URLs
 * Centralized configuration for backend API endpoints
 */

// Backend API base URL (adjust based on environment)
export const API_BASE_URL = '/api/v1';

// API Endpoints
export const API_ENDPOINTS = {
  // QUAD Reasoning Engine
  reasoning: (symbol: string) => `/recommendations/${symbol}/reasoning`,

  // Legacy endpoints (existing)
  stockData: (symbol: string) => `/stocks/${symbol}`,
  technicals: (symbol: string) => `/technicals/${symbol}`,
  derivatives: (symbol: string) => `/derivatives/${symbol}`,
  insider: (symbol: string) => `/insider/${symbol}`,
} as const;

// Helper function to build full URL
export const buildApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};
