/**
 * Position Reconciliation API Service
 */

import { ReconciliationRun, Discrepancy, ReconciliationReport } from '@/types/reconciliation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ReconciliationAPI {
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

  async triggerReconciliation(broker?: string): Promise<ReconciliationRun> {
    const params = broker ? `?broker=${broker}` : '';
    return this.request<ReconciliationRun>(`/api/v1/reconciliation/run${params}`, {
      method: 'POST',
    });
  }

  async listRuns(limit: number = 10): Promise<ReconciliationRun[]> {
    return this.request<ReconciliationRun[]>(`/api/v1/reconciliation/runs?limit=${limit}`);
  }

  async listDiscrepancies(hours: number = 24, resolved?: boolean): Promise<Discrepancy[]> {
    const params = new URLSearchParams({ hours: hours.toString() });
    if (resolved !== undefined) {
      params.append('resolved', resolved.toString());
    }
    return this.request<Discrepancy[]>(`/api/v1/reconciliation/discrepancies?${params}`);
  }

  async getReport(runId: number): Promise<ReconciliationReport> {
    return this.request<ReconciliationReport>(`/api/v1/reconciliation/report/${runId}`);
  }

  async resolveDiscrepancy(id: number, action: string): Promise<Discrepancy> {
    return this.request<Discrepancy>(`/api/v1/reconciliation/discrepancies/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_action: action }),
    });
  }
}

export const reconciliationAPI = new ReconciliationAPI();
