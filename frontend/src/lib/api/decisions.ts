import api from './client';

// Decision Types
export interface CausalFactor {
    cause: string;
    effect: string;
    confidence: number;
    magnitude?: number;
    type?: string;
    value?: string;
    contribution?: number;
}

export interface DecisionInputs {
    price: number;
    indicators: Record<string, number>;
    regime: string;
    ml?: {
        prediction: string;
        confidence: number;
        shadow_mode: boolean;
    };
}

export interface DecisionOutput {
    action: string;
    position_size?: number;
    limit_price?: number;
}

export interface Decision {
    decision_id: string;
    timestamp: string;
    strategy_id: number;
    symbol: string;
    mode: string;
    final_decision: string;
    conviction: number;
    inputs: DecisionInputs;
    weights: Record<string, number>;
    risk_checks: Record<string, string>;
    causal_graph: CausalFactor[];
    output: DecisionOutput;
    executed: boolean;
    execution_price?: number;
    execution_time?: string;
    actual_pnl?: number;
    was_correct?: boolean;
    tags: string[];
}

export interface RecordDecisionRequest {
    strategy_id: number;
    symbol: string;
    mode?: string;
    inputs: DecisionInputs;
    output: DecisionOutput;
    weights: Record<string, number>;
    risk_checks: Record<string, string>;
    causal_graph: CausalFactor[];
    notes?: string;
    tags?: string[];
}

export interface TimelinePoint {
    timestamp: string;
    decision: string;
    conviction: number;
    price?: number;
    regime?: string;
    executed: boolean;
    pnl?: number;
}

// Decision API Service
export const decisionApi = {
    // Record a new decision
    recordDecision: async (request: RecordDecisionRequest): Promise<Decision> => {
        const response = await api.post('/decisions/record', request);
        return response.data;
    },

    // Get single decision
    getDecision: async (decisionId: string): Promise<Decision> => {
        const response = await api.get(`/decisions/decision/${decisionId}`);
        return response.data;
    },

    // Get decisions by symbol
    getDecisionsBySymbol: async (
        symbol: string,
        mode?: string,
        limit: number = 50
    ): Promise<{ symbol: string; count: number; decisions: Decision[] }> => {
        const response = await api.get(`/decisions/symbol/${symbol}`, {
            params: { mode, limit },
        });
        return response.data;
    },

    // Get decisions by strategy
    getDecisionsByStrategy: async (
        strategyId: number,
        limit: number = 50
    ): Promise<{ strategy_id: number; count: number; decisions: Decision[] }> => {
        const response = await api.get(`/decisions/strategy/${strategyId}`, {
            params: { limit },
        });
        return response.data;
    },

    // Get decision timeline
    getTimeline: async (
        symbol: string,
        days: number = 30
    ): Promise<{ symbol: string; days: number; timeline: TimelinePoint[] }> => {
        const response = await api.get(`/decisions/timeline/${symbol}`, {
            params: { days },
        });
        return response.data;
    },

    // Update execution
    updateExecution: async (
        decisionId: string,
        executionPrice: number,
        executionStatus: string
    ): Promise<void> => {
        await api.put(`/decisions/decision/${decisionId}/execution`, {
            execution_price: executionPrice,
            execution_status: executionStatus,
        });
    },

    // Update outcome
    updateOutcome: async (
        decisionId: string,
        actualPnl: number,
        exitPrice: number,
        wasCorrect?: boolean
    ): Promise<void> => {
        await api.put(`/decisions/decision/${decisionId}/outcome`, {
            actual_pnl: actualPnl,
            exit_price: exitPrice,
            was_correct: wasCorrect,
        });
    },

    // Get causal analysis
    getCausalAnalysis: async (decisionId: string): Promise<any> => {
        const response = await api.get(`/decisions/decision/${decisionId}/causal-analysis`);
        return response.data;
    },
};
