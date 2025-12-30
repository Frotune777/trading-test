import api from './client';

export interface ConvictionPoint {
    timestamp: string;
    conviction: number;
    signal: string;
}

export interface ConvictionTimeline {
    symbol: string;
    historical: ConvictionPoint[];
    predicted?: ConvictionPoint[];
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

export interface PredictionResponse {
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

export interface AccuracyMetrics {
    symbol: string;
    total_signals: number;
    correct_signals: number;
    win_rate: number;
    rolling_win_rates: Record<string, number>;
    avg_conviction_winning: number;
    avg_conviction_losing: number;
    total_profit_loss: number;
    best_signal?: any;
    worst_signal?: any;
}

export interface PeerInfo {
    symbol: string;
    conviction: number;
    rank: number;
    signal: string;
    is_self: boolean;
}

export interface PeerComparison {
    symbol: string;
    rank: number;
    total_peers: number;
    avg_sector_conviction: number;
    sector: string;
    peers: PeerInfo[];
    error?: string;
}

export interface PillarWeights {
    trend: number;
    momentum: number;
    volatility: number;
    liquidity: number;
    sentiment: number;
    regime: number;
}

export const analyticsApi = {
    // Timeline & Predictions
    getTimeline: async (symbol: string, days: number = 30): Promise<ConvictionTimeline> => {
        const response = await api.get(`/quad/${symbol}/timeline`, { params: { days } });
        return response.data;
    },

    predict: async (symbol: string, pillars: any, daysAhead: number = 7): Promise<PredictionResponse> => {
        const response = await api.post(`/quad/${symbol}/predict`, pillars, { params: { days_ahead: daysAhead } });
        return response.data;
    },

    // Correlations & Drift
    getCorrelations: async (symbol: string, days: number = 90): Promise<CorrelationMatrix> => {
        const response = await api.get(`/quad/${symbol}/correlations`, { params: { days } });
        return response.data;
    },

    calculateDrift: async (symbol: string, pillars: any): Promise<PillarDriftAnalysis> => {
        const response = await api.post(`/quad/${symbol}/drift`, pillars);
        return response.data;
    },

    // Accuracy
    getAccuracy: async (symbol: string, days: number = 90): Promise<AccuracyMetrics> => {
        const response = await api.get(`/quad/${symbol}/accuracy`, { params: { days } });
        return response.data;
    },

    // Peer Comparison
    getPeers: async (symbol: string): Promise<PeerComparison> => {
        const response = await api.get(`/quad/${symbol}/peers`);
        return response.data;
    },

    // Configuration (Weights)
    getWeights: async (): Promise<PillarWeights> => {
        const response = await api.get('/preferences/weights');
        return response.data;
    },

    setWeights: async (weights: PillarWeights): Promise<{ status: string; weights: PillarWeights }> => {
        const response = await api.post('/preferences/weights', { weights });
        return response.data;
    },

    resetWeights: async (): Promise<{ status: string; message: string }> => {
        const response = await api.post('/preferences/reset');
        return response.data;
    },
};
