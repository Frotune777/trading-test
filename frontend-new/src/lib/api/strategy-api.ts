/**
 * Strategy Management API Service
 * Communicates with backend strategy endpoints
 */

import { Strategy, StrategyCreate, StrategyUpdate, SymbolMapping, SymbolMappingCreate } from '@/types/strategy';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class StrategyAPI {
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

  async createStrategy(data: StrategyCreate): Promise<Strategy> {
    return this.request<Strategy>('/api/v1/strategy', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listStrategies(): Promise<Strategy[]> {
    return this.request<Strategy[]>('/api/v1/strategy');
  }

  async getStrategy(id: number): Promise<Strategy> {
    return this.request<Strategy>(`/api/v1/strategy/${id}`);
  }

  async updateStrategy(id: number, data: StrategyUpdate): Promise<Strategy> {
    return this.request<Strategy>(`/api/v1/strategy/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async toggleStrategy(id: number): Promise<Strategy> {
    return this.request<Strategy>(`/api/v1/strategy/${id}/toggle`, {
      method: 'POST',
    });
  }

  async deleteStrategy(id: number): Promise<void> {
    await this.request<void>(`/api/v1/strategy/${id}`, {
      method: 'DELETE',
    });
  }

  async addSymbol(strategyId: number, data: SymbolMappingCreate): Promise<SymbolMapping> {
    return this.request<SymbolMapping>(`/api/v1/strategy/${strategyId}/symbols`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSymbols(strategyId: number): Promise<SymbolMapping[]> {
    return this.request<SymbolMapping[]>(`/api/v1/strategy/${strategyId}/symbols`);
  }

  async deleteSymbol(strategyId: number, symbolId: number): Promise<void> {
    await this.request<void>(`/api/v1/strategy/${strategyId}/symbols/${symbolId}`, {
      method: 'DELETE',
    });
  }
}

export const strategyAPI = new StrategyAPI();
