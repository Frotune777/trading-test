import api from './client';

export interface FeedHealthStatus {
    status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' | 'UNKNOWN';
    components: {
        redis: boolean;
        openalgo: boolean;
        database: boolean;
    };
    timestamp: string;
}

export interface PipelineMetrics {
    circuit_breaker_active: boolean;
    consecutive_failures: number;
}

export interface FeedHealthMetrics {
    overall_status: string;
    components: any;
    metrics: {
        active_symbols: number;
        stale_symbols: number;
        average_latency: number;
        pipeline: PipelineMetrics;
    };
    timestamp: string;
}

export const feedHealthApi = {
    // Get quick status
    getStatus: async (): Promise<FeedHealthStatus> => {
        const response = await api.get('/feed-health/status');
        return response.data;
    },

    // Get detailed metrics
    getMetrics: async (): Promise<FeedHealthMetrics> => {
        const response = await api.get('/feed-health/metrics');
        return response.data;
    },

    // Get history
    getHistory: async (limit: number = 20): Promise<FeedHealthStatus[]> => {
        const response = await api.get('/feed-health/history', { params: { limit } });
        return response.data;
    },

    // Reset circuit breaker
    resetCircuitBreaker: async (): Promise<void> => {
        await api.post('/feed-health/circuit-breaker/reset');
    },

    // Start monitoring
    startMonitor: async (): Promise<void> => {
        await api.post('/feed-health/monitor/start');
    },

    // Stop monitoring
    stopMonitor: async (): Promise<void> => {
        await api.post('/feed-health/monitor/stop');
    },
};
