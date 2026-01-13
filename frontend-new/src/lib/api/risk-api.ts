/**
 * Risk Metrics API Service
 * TypeScript client for Risk Management backend
 */

import { API_BASE_URL } from '../api-config';

// ==================== Types ====================

export interface RiskValue {
  symbol: string;
  calculated_at: string;
  days: number;
}

export interface VaRResponse extends RiskValue {
  var: number;
  confidence: number;
  value: string;
  label: string;
  description: string;
  color: string;
}

export interface BetaResponse extends RiskValue {
  beta: number;
  market_symbol: string;
  value: string;
  label: string;
  description: string;
}

export interface SharpeResponse extends RiskValue {
  sharpe_ratio: number;
  risk_free_rate: number;
  value: string;
  rating: string;
  description: string;
}

export interface FullRiskMetrics {
  symbol: string;
  calculated_at: string;
  data_points_used: number;
  var: {
    "95_30d": number | null;
    "99_30d": number | null;
    "95_60d": number | null;
    "99_60d": number | null;
    "95_90d": number | null;
    "99_90d": number | null;
  };
  beta: {
    "30d": number | null;
    "60d": number | null;
    "252d": number | null;
  };
  sharpe: {
    "30d": number | null;
    "60d": number | null;
    "252d": number | null;
  };
  volatility: {
    "30d": number | null;
    "60d": number | null;
    "252d": number | null;
  };
}

// ==================== API Client ====================

class RiskAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/risk`;
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
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get Value at Risk (VaR)
   */
  async getVaR(symbol: string, days: number = 30, confidence: number = 0.95): Promise<VaRResponse> {
    return this.request(`/${symbol}/var?days=${days}&confidence=${confidence}`);
  }

  /**
   * Get Beta relative to market
   */
  async getBeta(symbol: string, days: number = 252, marketSymbol: string = 'NIFTY'): Promise<BetaResponse> {
    return this.request(`/${symbol}/beta?days=${days}&market_symbol=${marketSymbol}`);
  }

  /**
   * Get Sharpe Ratio (Risk-adjusted return)
   */
  async getSharpeRatio(symbol: string, days: number = 252, riskFreeRate: number = 0.065): Promise<SharpeResponse> {
    return this.request(`/${symbol}/sharpe?days=${days}&risk_free_rate=${riskFreeRate}`);
  }

  /**
   * Get all risk metrics (calculated/updated on fly)
   */
  async getAllMetrics(symbol: string): Promise<FullRiskMetrics> {
    return this.request(`/${symbol}/all`);
  }

  /**
   * Get latest cached risk metrics
   */
  async getLatestMetrics(symbol: string): Promise<FullRiskMetrics> {
    return this.request(`/${symbol}/latest`);
  }
}

// Export singleton instance
export const riskAPI = new RiskAPI();
