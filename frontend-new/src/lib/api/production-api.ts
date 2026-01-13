/**
 * Production Features API Service
 * Risk, Analytics, Sandbox, Monitoring, Audit
 */

import {
  RiskValidationResult,
  BrokerAnalytics,
  StrategyAnalytics,
  SandboxPortfolio,
  SystemHealth,
  AuditLog
} from '@/types/production';

const API_BASE = '/api/v1';

class ProductionAPI {
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

  // Risk Management
  async validateOrderRisk(order: any): Promise<RiskValidationResult> {
    return this.request<RiskValidationResult>('/production/risk/validate', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  // Execution Analytics
  async getBrokerAnalytics(broker: string, hours: number = 24): Promise<BrokerAnalytics> {
    return this.request<BrokerAnalytics>(`/production/analytics/broker/${broker}?hours=${hours}`);
  }

  async getStrategyAnalytics(strategyId: number, days: number = 7): Promise<StrategyAnalytics> {
    return this.request<StrategyAnalytics>(`/production/analytics/strategy/${strategyId}?days=${days}`);
  }

  // Sandbox Mode
  async enableSandbox(): Promise<{ status: string; message: string }> {
    return this.request('/production/sandbox/enable', {
      method: 'POST',
    });
  }

  async disableSandbox(): Promise<{ status: string; message: string }> {
    return this.request('/production/sandbox/disable', {
      method: 'POST',
    });
  }

  async getSandboxPortfolio(): Promise<SandboxPortfolio> {
    return this.request<SandboxPortfolio>('/production/sandbox/portfolio');
  }

  async resetSandbox(): Promise<{ status: string; message: string }> {
    return this.request('/production/sandbox/reset', {
      method: 'POST',
    });
  }

  // Monitoring
  async getSystemHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/monitoring/health');
  }

  async getSystemMetrics(): Promise<any> {
    return this.request('/monitoring/latency/stats');
  }

  // Audit Logs
  async queryAuditLogs(params: {
    event_type?: string;
    strategy_id?: number;
    hours?: number;
    limit?: number;
  }): Promise<{ total: number; logs: AuditLog[] }> {
    const searchParams = new URLSearchParams();
    if (params.event_type) searchParams.append('event_type', params.event_type);
    if (params.strategy_id) searchParams.append('strategy_id', params.strategy_id.toString());
    if (params.hours) searchParams.append('hours', params.hours.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());

    return this.request(`/production/audit/logs?${searchParams}`);
  }
}

export const productionAPI = new ProductionAPI();
