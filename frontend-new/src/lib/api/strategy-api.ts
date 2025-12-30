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

  // Code Management Methods
  async validateCode(code: string): Promise<ValidationResult> {
    return this.request<ValidationResult>('/api/v1/strategy/validate-code', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  }

  async getStrategyCode(id: number): Promise<StrategyCodeResponse> {
    return this.request<StrategyCodeResponse>(`/api/v1/strategy/${id}/code`);
  }

  async updateStrategyCode(id: number, code: string): Promise<StrategyCodeUpdateResponse> {
    return this.request<StrategyCodeUpdateResponse>(`/api/v1/strategy/${id}/code`, {
      method: 'PUT',
      body: JSON.stringify({ code }),
    });
  }

  async backtestStrategy(id: number, request: BacktestRequest): Promise<BacktestResponse> {
    return this.request<BacktestResponse>(`/api/v1/strategy/${id}/backtest`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

// Type definitions
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  timestamp: string;
}

export interface StrategyCodeResponse {
  strategy_id: number;
  name: string;
  code: string;
  platform: string;
}

export interface StrategyCodeUpdateResponse {
  strategy_id: number;
  name: string;
  code: string;
  updated_at: string;
  validation: ValidationResult;
}

export interface BacktestRequest {
  symbol: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  slippage_pct?: number;
  commission_fixed?: number;
  params?: Record<string, any>;
}

export interface BacktestResponse {
  symbol: string;
  total_trades: number;
  equity_curve: Array<{ date: string; value: number }>;
  trades: Array<Record<string, any>>;
  final_capital: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  max_drawdown: number;
  error?: string;
}


export const strategyAPI = new StrategyAPI();

