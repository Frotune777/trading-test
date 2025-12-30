import api from './client';

// TA Configuration Types
export interface TAWeights {
    trend: number;
    momentum: number;
    volatility: number;
    volume: number;
}

export interface RegimeWeights {
    TRENDING_UP: TAWeights;
    TRENDING_DOWN: TAWeights;
    RANGING: TAWeights;
    VOLATILE: TAWeights;
    UNKNOWN: TAWeights;
}

export interface TAAccuracy {
    overall_accuracy: number;
    best_regime: string;
    worst_regime: string;
    sample_size: number;
    regime_breakdown: Record<string, number>;
}

export interface TAPerformance {
    category: string;
    accuracy: number;
    signals: number;
    regime: string;
}

// TA API Service
export const taApi = {
    // Get all regime weights
    getWeights: async (): Promise<RegimeWeights> => {
        const response = await api.get('/ta/weights');
        return response.data;
    },

    // Update weights for a specific regime
    updateWeights: async (regime: string, weights: TAWeights): Promise<void> => {
        await api.put(`/ta/weights/${regime}`, weights);
    },

    // Get historical accuracy
    getAccuracy: async (days: number = 30): Promise<TAAccuracy> => {
        const response = await api.get('/ta/accuracy', { params: { days } });
        return response.data;
    },

    // Get indicator performance
    getPerformance: async (): Promise<TAPerformance[]> => {
        const response = await api.get('/ta/performance');
        return response.data;
    },
};
