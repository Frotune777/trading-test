/**
 * User Preferences API Service
 * TypeScript client for managing user preferences (e.g., QUAD weights)
 */

import { API_BASE_URL } from '../api-config';

export interface QUADWeights {
  trend: number;
  momentum: number;
  volatility: number;
  liquidity: number;
  sentiment: number;
  regime: number;
}

class PreferencesAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/preferences`;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async getWeights(): Promise<QUADWeights> {
    return this.request('/weights');
  }

  async setWeights(weights: QUADWeights): Promise<{ status: string; weights: QUADWeights }> {
    return this.request('/weights', {
      method: 'POST',
      body: JSON.stringify({ weights }),
    });
  }

  async resetWeights(): Promise<{ status: string; message: string }> {
    return this.request('/reset', {
      method: 'POST',
    });
  }
}

export const preferencesAPI = new PreferencesAPI();
