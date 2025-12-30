import api from './client';

// Strategy Types
export interface Strategy {
    id: number;
    name: string;
    description: string;
    type: 'technical' | 'fundamental' | 'hybrid';
    platform: string;
    is_active: boolean;
    user_id: string;
    created_at: string;
    updated_at: string;
    strategy_code?: string;
}

export interface StrategyCode {
    strategy_id: number;
    name: string;
    code: string;
    platform: string;
}

export interface CodeValidation {
    valid: boolean;
    errors: string[];
    warnings: string[];
    timestamp: string;
}

export interface BacktestRequest {
    symbol: string;
    start_date?: string;
    end_date?: string;
    initial_capital?: number;
    slippage_pct?: number;
    commission_fixed?: number;
    params?: Record<string, any>;
}

export interface BacktestResult {
    symbol: string;
    total_trades: number;
    equity_curve: Array<{ date: string; value: number }>;
    trades: Array<{
        entry_date: string;
        exit_date: string;
        pnl: number;
        pnl_pct: number;
        signal: string;
        conviction?: number;
    }>;
    final_capital: number;
    sharpe: number;
    sortino: number;
    calmar: number;
    max_drawdown: number;
    error?: string;
}

// Strategy API Service
export const strategyApi = {
    // List all strategies
    getStrategies: async (): Promise<Strategy[]> => {
        const response = await api.get('/strategy');
        return response.data;
    },

    // Get single strategy
    getStrategy: async (id: number): Promise<Strategy> => {
        const response = await api.get(`/strategy/${id}`);
        return response.data;
    },

    // Create strategy
    createStrategy: async (data: Partial<Strategy>): Promise<Strategy> => {
        const response = await api.post('/strategy', data);
        return response.data;
    },

    // Update strategy
    updateStrategy: async (id: number, data: Partial<Strategy>): Promise<Strategy> => {
        const response = await api.put(`/strategy/${id}`, data);
        return response.data;
    },

    // Delete strategy
    deleteStrategy: async (id: number): Promise<void> => {
        await api.delete(`/strategy/${id}`);
    },

    // Toggle strategy active status
    toggleStrategy: async (id: number): Promise<void> => {
        await api.post(`/strategy/${id}/toggle`);
    },

    // Get strategy code
    getCode: async (id: number): Promise<StrategyCode> => {
        const response = await api.get(`/strategy/${id}/code`);
        return response.data;
    },

    // Update strategy code
    updateCode: async (id: number, code: string): Promise<void> => {
        await api.put(`/strategy/${id}/code`, { code });
    },

    // Validate code
    validateCode: async (code: string): Promise<CodeValidation> => {
        const response = await api.post('/strategy/validate-code', { code });
        return response.data;
    },

    // Run backtest
    backtest: async (id: number, request: BacktestRequest): Promise<BacktestResult> => {
        const response = await api.post(`/strategy/${id}/backtest`, request);
        return response.data;
    },
};
