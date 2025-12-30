import api from './client';

export interface RiskLimits {
    max_positions: number;
    max_position_size: number;
    max_portfolio_value: number;
    max_daily_loss: number;
    max_weekly_loss: number;
    max_drawdown_pct: number;
    max_sector_concentration_pct: number;
    max_single_stock_pct: number;
}

export interface RiskMetrics {
    total_pnl: number;
    daily_pnl: number;
    weekly_pnl: number;
    unrealized_pnl: number;
    realized_pnl: number;
    position_count: number;
    total_exposure: number;
    portfolio_value: number;
    current_drawdown_pct: number;
    concentration_by_symbol: Record<string, number>;
}

export interface KillSwitchStatus {
    enabled: boolean;
    reason?: string;
    activated_at?: string;
    activated_by?: string;
}

export interface Alert {
    id: number;
    timestamp: string;
    alert_type: 'CRITICAL' | 'WARNING' | 'INFO';
    category: string;
    title: string;
    message: string;
    related_symbol?: string;
    acknowledged: boolean;
}

export interface RiskDashboardData extends RiskMetrics {
    limits: RiskLimits;
    utilization: {
        position_limit: number;
        daily_loss_limit: number;
        weekly_loss_limit: number;
    };
    kill_switch: KillSwitchStatus;
    alerts: Alert[];
}

export interface KillSwitchRequest {
    reason: string;
    confirmed: boolean;
}

export const riskApi = {
    // Get complete dashboard data
    getDashboard: async (): Promise<RiskDashboardData> => {
        const response = await api.get('/risk/dashboard');
        return response.data;
    },

    // Get current limits
    getLimits: async (): Promise<RiskLimits> => {
        const response = await api.get('/risk/limits');
        return response.data;
    },

    // Update limits
    updateLimits: async (limits: Partial<RiskLimits>): Promise<RiskLimits> => {
        const response = await api.put('/risk/limits', limits);
        return response.data.limits;
    },

    // Activate kill switch
    activateKillSwitch: async (data: KillSwitchRequest): Promise<void> => {
        await api.post('/risk/kill-switch/activate', data);
    },

    // Deactivate kill switch
    deactivateKillSwitch: async (reason: string): Promise<void> => {
        await api.post('/risk/kill-switch/deactivate', { reason });
    },

    // Check limits
    checkLimits: async (): Promise<{ breaches: any[]; has_breaches: boolean }> => {
        const response = await api.get('/risk/check-limits');
        return response.data;
    },

    // Acknowledge alert
    acknowledgeAlert: async (alertId: number): Promise<void> => {
        await api.post('/risk/alerts/acknowledge', { alert_id: alertId });
    },
};
