/**
 * TA Aggregator Configuration API Service
 */

const API_BASE = '/api/v1';

class TAConfigAPI {
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

    async getAllWeights(): Promise<Record<string, Record<string, number>>> {
        return this.request<Record<string, Record<string, number>>>('/ta/weights');
    }

    async updateRegimeWeights(regime: string, weights: Record<string, number>): Promise<any> {
        return this.request<any>(`/ta/weights/${regime}`, {
            method: 'PUT',
            body: JSON.stringify(weights),
        });
    }

    async getAccuracyMetrics(days: number = 30): Promise<any> {
        return this.request<any>(`/ta/accuracy?days=${days}`);
    }

    async getIndicatorPerformance(): Promise<any[]> {
        return this.request<any[]>('/ta/performance');
    }
}

export const taConfigAPI = new TAConfigAPI();
