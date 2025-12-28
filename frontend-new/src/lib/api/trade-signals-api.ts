/**
 * Trade Signals API Service
 * TypeScript client for actionable trade parameters
 */

import { API_BASE_URL } from '../api-config';

// ==================== Types ====================

export interface PivotSet {
  pivot: number;
  s1: number;
  s2: number;
  s3?: number;
  r1: number;
  r2: number;
  r3?: number;
}

export interface Zone {
  label: string;
  level: number;
  strength: 'Moderate' | 'Strong' | 'Very Strong';
}

export interface TradeSetup {
  symbol: string;
  current_price: number;
  pivots: {
    standard: PivotSet;
    fibonacci: PivotSet;
  };
  zones: {
    support: Zone[];
    resistance: Zone[];
  };
  parameters: {
    stop_loss: number;
    take_profit_1: number;
    take_profit_2: number;
    risk_reward_ratio: number;
    atr: number;
    var_risk: number;
  };
  position_sizing: {
    account_size: number;
    risk_per_trade_pct: number;
    recommended_shares: number;
    kelly_allocation_pct: number;
    capital_required: number;
  };
}

// ==================== API Client ====================

class TradeSignalsAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/trade-signals`;
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
   * Get trade setup including SL/TP and S/R zones
   */
  async getTradeSetup(symbol: string, price?: number): Promise<TradeSetup> {
    const query = price ? `?price=${price}` : '';
    return this.request(`/${symbol}/setup${query}`);
  }
}

// Export singleton instance
export const tradeSignalsAPI = new TradeSignalsAPI();
