'use client';

import { useState, useEffect } from 'react';
import { FileDown, Filter, Calendar, User, Activity } from 'lucide-react';
import { AuditAPI, AuditLogEntry, AuditTrailFilters } from '@/lib/api/audit';
import { downloadCSV } from '@/lib/utils/export';
import { DashboardSkeleton } from '../common/LoadingSkeleton';

const ACTION_TYPE_COLORS: Record<string, string> = {
    ORDER_PLACED: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    ORDER_CANCELLED: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
    STRATEGY_ENABLED: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    STRATEGY_DISABLED: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    KILL_SWITCH_ACTIVATED: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    RISK_LIMIT_CHANGED: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
    DATA_INGESTED: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
    OTHER: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
};

export function AuditTrail() {
    const [logs, setLogs] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState<AuditTrailFilters>({
        limit: 100,
        offset: 0,
    });
    const [showFilters, setShowFilters] = useState(false);

    useEffect(() => {
        fetchAuditLogs();
    }, [filters]);

    const fetchAuditLogs = async () => {
        try {
            setLoading(true);
            const data = await AuditAPI.getAuditTrail(filters);
            setLogs(data.logs || data || []);
        } catch (error) {
            console.error('Error fetching audit logs:', error);
            // Mock data for development
            setLogs([
                {
                    id: '1',
                    timestamp: new Date().toISOString(),
                    user_id: 'user123',
                    action_type: 'ORDER_PLACED',
                    entity_type: 'ORDER',
                    entity_id: 'ORD001',
                    description: 'Placed BUY order for RELIANCE',
                    metadata: { symbol: 'RELIANCE', quantity: 10, price: 2500 },
                },
                {
                    id: '2',
                    timestamp: new Date(Date.now() - 3600000).toISOString(),
                    user_id: 'user123',
                    action_type: 'STRATEGY_ENABLED',
                    entity_type: 'STRATEGY',
                    entity_id: 'STR001',
                    description: 'Enabled strategy: SMA Crossover',
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            // Export current filtered logs to CSV
            downloadCSV(logs, `audit_trail_${Date.now()}.csv`);
        } catch (error) {
            console.error('Error exporting audit trail:', error);
        }
    };

    if (loading) {
        return <DashboardSkeleton />;
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black text-gray-900 dark:text-white uppercase tracking-tight">
                        Audit Trail
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">
                        Complete history of all system actions for compliance
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-xl font-semibold hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
                    >
                        <Filter className="w-4 h-4" />
                        Filters
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/20"
                    >
                        <FileDown className="w-4 h-4" />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Filters Panel */}
            {showFilters && (
                <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Start Date
                            </label>
                            <input
                                type="date"
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white"
                                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                End Date
                            </label>
                            <input
                                type="date"
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white"
                                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Action Type
                            </label>
                            <select
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white"
                                onChange={(e) => setFilters({ ...filters, action_type: e.target.value || undefined })}
                            >
                                <option value="">All Actions</option>
                                <option value="ORDER_PLACED">Order Placed</option>
                                <option value="ORDER_CANCELLED">Order Cancelled</option>
                                <option value="STRATEGY_ENABLED">Strategy Enabled</option>
                                <option value="STRATEGY_DISABLED">Strategy Disabled</option>
                                <option value="KILL_SWITCH_ACTIVATED">Kill Switch</option>
                                <option value="RISK_LIMIT_CHANGED">Risk Limit Changed</option>
                            </select>
                        </div>
                    </div>
                </div>
            )}

            {/* Audit Logs Table */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                    Timestamp
                                </th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                    Action
                                </th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                    Description
                                </th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                    Entity
                                </th>
                                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                                    User
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {logs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                                        No audit logs found
                                    </td>
                                </tr>
                            ) : (
                                logs.map((log) => (
                                    <tr
                                        key={log.id}
                                        className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
                                                <Calendar className="w-4 h-4 text-gray-400" />
                                                {new Date(log.timestamp).toLocaleString()}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span
                                                className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${ACTION_TYPE_COLORS[log.action_type] || ACTION_TYPE_COLORS.OTHER
                                                    }`}
                                            >
                                                {log.action_type.replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 dark:text-white">
                                                {log.description}
                                            </div>
                                            {log.metadata && (
                                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                    {JSON.stringify(log.metadata)}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                                <Activity className="w-4 h-4" />
                                                {log.entity_type}
                                                {log.entity_id && (
                                                    <span className="text-xs text-gray-400">#{log.entity_id}</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                                <User className="w-4 h-4" />
                                                {log.user_id}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Stats Footer */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                        Showing <span className="font-bold text-gray-900 dark:text-white">{logs.length}</span> audit entries
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                        Audit logs are retained for 90 days for compliance
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AuditTrail;
