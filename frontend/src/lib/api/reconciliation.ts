import api from './client';

export interface Discrepancy {
    id: number;
    run_id: number;
    symbol: string;
    internal_qty: number;
    broker_qty: number;
    difference_qty: number;
    internal_pnl: number;
    broker_pnl: number;
    difference_pnl: number;
    discrepancy_type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    resolved: boolean;
    resolution_action?: string;
    resolution_method?: string;
    resolved_at?: string;
    created_at: string;
}

export interface ReconciliationRun {
    id: number;
    broker_type: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    started_at: string;
    completed_at?: string;
    positions_checked: number;
    discrepancies_found: number;
    error_message?: string;
}

export const reconciliationApi = {
    // Trigger manual reconciliation
    triggerRun: async (broker?: string): Promise<ReconciliationRun> => {
        const response = await api.post('/reconciliation/run', null, {
            params: { broker }
        });
        return response.data;
    },

    // List recent runs
    getRuns: async (limit: number = 10): Promise<ReconciliationRun[]> => {
        const response = await api.get('/reconciliation/runs', {
            params: { limit }
        });
        return response.data;
    },

    // List discrepancies
    getDiscrepancies: async (hours: number = 24, resolved?: boolean): Promise<Discrepancy[]> => {
        const response = await api.get('/reconciliation/discrepancies', {
            params: { hours, resolved }
        });
        return response.data;
    },

    // Get run report
    getReport: async (runId: number): Promise<any> => {
        const response = await api.get(`/reconciliation/report/${runId}`);
        return response.data;
    },

    // Resolve discrepancy
    resolveDiscrepancy: async (id: number, action: string): Promise<Discrepancy> => {
        const response = await api.post(`/reconciliation/discrepancies/${id}/resolve`, null, {
            params: { resolution_action: action }
        });
        return response.data;
    },
};
