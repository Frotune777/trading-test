import api from './client';

/**
 * Audit Trail API Client
 * Endpoints for compliance and audit logging
 */

export interface AuditLogEntry {
    id: string;
    timestamp: string;
    user_id: string;
    action_type: 'ORDER_PLACED' | 'ORDER_CANCELLED' | 'STRATEGY_ENABLED' | 'STRATEGY_DISABLED' | 'KILL_SWITCH_ACTIVATED' | 'RISK_LIMIT_CHANGED' | 'DATA_INGESTED' | 'OTHER';
    entity_type: 'ORDER' | 'STRATEGY' | 'RISK' | 'DATA' | 'SYSTEM';
    entity_id?: string;
    description: string;
    metadata?: Record<string, any>;
    ip_address?: string;
}

export interface AuditTrailFilters {
    start_date?: string;
    end_date?: string;
    user_id?: string;
    action_type?: string;
    entity_type?: string;
    limit?: number;
    offset?: number;
}

export const AuditAPI = {
    /**
     * Get audit trail with optional filters
     */
    getAuditTrail: async (filters?: AuditTrailFilters) => {
        const response = await api.get('/audit/trail', { params: filters });
        return response.data;
    },

    /**
     * Get audit log entry by ID
     */
    getAuditEntry: async (id: string) => {
        const response = await api.get(`/audit/trail/${id}`);
        return response.data;
    },

    /**
     * Export audit trail to CSV
     */
    exportAuditTrail: async (filters?: AuditTrailFilters) => {
        const response = await api.get('/audit/export', {
            params: filters,
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Log a custom audit event (if backend supports)
     */
    logAuditEvent: async (event: Partial<AuditLogEntry>) => {
        const response = await api.post('/audit/log', event);
        return response.data;
    },
};

export default AuditAPI;
