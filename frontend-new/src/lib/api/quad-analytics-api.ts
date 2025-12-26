/**
 * QUAD Analytics API Service
 * TypeScript client for QUAD analytics backend
 */

import { API_BASE_URL } from '../api-config';

// ==================== Types ====================

export interface PillarScores {
  trend: number;
  momentum: number;
  volatility: number;
  liquidity: number;
  sentiment: number;
  regime: number;
}

export interface QUADDecision {
  id: number;
  symbol: string;
  timestamp: string;
  conviction: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  pillars: PillarScores;
  reasoning_summary?: string;
  current_price?: number;
  volume?: number;
  created_at: string;
}

export interface ConvictionTimelinePoint {
  timestamp: string;
  conviction: number;
  signal: string;
}

export interface ConvictionTimeline {
  symbol: string;
  historical: ConvictionTimelinePoint[];
  predicted?: ConvictionTimelinePoint[];
  volatility?: number;
}

export interface PillarDrift {
  pillar: string;
  previous_score: number;
  current_score: number;
  delta: number;
  percent_change: number;
  previous_bias: string;
  current_bias: string;
  significant: boolean;
}

export interface PillarDriftAnalysis {
  symbol: string;
  current_timestamp: string;
  previous_timestamp: string;
  drifts: PillarDrift[];
  total_drift: number;
}

export interface QUADPrediction {
  symbol: string;
  predicted_conviction: number;
  confidence_low: number;
  confidence_high: number;
  accuracy: number;
  model_version: string;
  prediction_days: number;
  timestamp: string;
}

export interface CorrelationPair {
  pillar1: string;
  pillar2: string;
  correlation: number;
  p_value?: number;
  significance: string;
}

export interface CorrelationMatrix {
  symbol: string;
  calculated_at: string;
  correlations: CorrelationPair[];
  sample_size: number;
  days_analyzed: number;
}

export interface SignalAccuracyMetrics {
  symbol: string;
  total_signals: number;
  correct_signals: number;
  win_rate: number;
  avg_conviction_winning: number;
  avg_conviction_losing: number;
  total_profit_loss: number;
  best_signal?: any;
  worst_signal?: any;
}

export interface QUADAlert {
  id: number;
  symbol: string;
  alert_type: string;
  threshold?: number;
  pillar_name?: string;
  active: boolean;
  triggered_at?: string;
  message?: string;
  channels: string[];
  created_at: string;
}

export interface CreateAlertRequest {
  symbol: string;
  alert_type: 'CONVICTION_ABOVE' | 'CONVICTION_BELOW' | 'PILLAR_DRIFT' | 'SIGNAL_CHANGE' | 'PREDICTION_CONFIDENCE_LOW';
  threshold?: number;
  pillar_name?: string;
  channels?: string[];
}

// ==================== API Client ====================

class QUADAnalyticsAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/quad`;
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

  // ==================== Decision Management ====================

  async storeDecision(decision: {
    symbol: string;
    conviction: number;
    signal: 'BUY' | 'SELL' | 'HOLD';
    pillars: PillarScores;
    reasoning_summary?: string;
    current_price?: number;
    volume?: number;
  }): Promise<QUADDecision> {
    return this.request('/decision', {
      method: 'POST',
      body: JSON.stringify(decision),
    });
  }

  async getDecisionHistory(
    symbol: string,
    params?: {
      limit?: number;
      signal_filter?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<QUADDecision[]> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/${symbol}/history?${query}`);
  }

  // ==================== Timeline & Drift ====================

  async getConvictionTimeline(
    symbol: string,
    days: number = 30
  ): Promise<ConvictionTimeline> {
    return this.request(`/${symbol}/timeline?days=${days}`);
  }

  async calculatePillarDrift(
    symbol: string,
    currentPillars: PillarScores
  ): Promise<PillarDriftAnalysis | null> {
    return this.request(`/${symbol}/drift`, {
      method: 'POST',
      body: JSON.stringify(currentPillars),
    });
  }

  // ==================== ML Predictions ====================

  async predictConviction(
    symbol: string,
    currentPillars: PillarScores,
    daysAhead: number = 7
  ): Promise<QUADPrediction | null> {
    return this.request(`/${symbol}/predict?days_ahead=${daysAhead}`, {
      method: 'POST',
      body: JSON.stringify(currentPillars),
    });
  }

  // ==================== Correlations ====================

  async getPillarCorrelations(
    symbol: string,
    days: number = 90
  ): Promise<CorrelationMatrix | null> {
    return this.request(`/${symbol}/correlations?days=${days}`);
  }

  // ==================== Signal Accuracy ====================

  async getSignalAccuracy(
    symbol: string,
    days: number = 90
  ): Promise<SignalAccuracyMetrics> {
    return this.request(`/${symbol}/accuracy?days=${days}`);
  }

  // ==================== Alerts ====================

  async createAlert(alert: CreateAlertRequest): Promise<QUADAlert> {
    return this.request('/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  }

  async listAlerts(params?: {
    symbol?: string;
    active_only?: boolean;
  }): Promise<QUADAlert[]> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/alerts?${query}`);
  }

  async deleteAlert(alertId: number): Promise<{ message: string }> {
    return this.request(`/alerts/${alertId}`, {
      method: 'DELETE',
    });
  }

  async acknowledgeAlert(alertId: number): Promise<{ message: string }> {
    return this.request(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const quadAnalyticsAPI = new QUADAnalyticsAPI();
