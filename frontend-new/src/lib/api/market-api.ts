/**
 * Market Data API Service
 * Indices, Breadth, Sentiment
 */

const API_BASE = '/api/v1';

export interface MarketIndex {
  name: string;
  value: number;
  change: number;
  change_percent: number;
  is_up: boolean;
  history?: number[]; // For sparklines
}

export interface MarketMood {
  score: number;
  status: 'Extreme Fear' | 'Fear' | 'Neutral' | 'Greed' | 'Extreme Greed';
  current_val: string;
  previous_val: string;
  previous_status: string;
}

export interface MarketBreadth {
  advances: number;
  declines: number;
  unchanged: number;
  index: string;
}

class MarketAPI {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  async getIndices(): Promise<{ data: MarketIndex[] }> {
    return this.request<{ data: MarketIndex[] }>('/market/indices');
  }

  async getMarketBreadth(): Promise<MarketBreadth> {
    return this.request<MarketBreadth>('/market/breadth');
  }

  async getMarketMood(): Promise<MarketMood> {
    // This will be a new endpoint in the backend
    try {
      return await this.request<MarketMood>('/market/mood');
    } catch (e) {
      // Fallback for demo if backend isn't updated yet
      console.warn('Market mood API failed, using fallback', e);
      return {
        score: 65,
        status: 'Greed',
        current_val: 'Greed',
        previous_val: 'Greed',
        previous_status: 'Greed'
      };
    }
  }

  async getHistory(symbol: string, days: number = 30): Promise<{ symbol: string; data: any[] }> {
    return this.request<{ symbol: string; data: any[] }>(`/market/history/${symbol}?days=${days}`);
  }

  async getVolumeProfile(symbol: string, days: number = 30, bins: number = 40): Promise<any> {
    return this.request<any>(`/market/volume-profile/${symbol}?days=${days}&bins=${bins}`);
  }
}

export const marketAPI = new MarketAPI();
