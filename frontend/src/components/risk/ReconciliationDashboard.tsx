'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reconciliationApi } from '@/lib/api/reconciliation';
import {
    RefreshCw, FileText, CheckCircle, AlertOctagon,
    ChevronRight, Clock, AlertTriangle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function ReconciliationDashboard() {
    const queryClient = useQueryClient();
    const [view, setView] = useState<'discrepancies' | 'history'>('discrepancies');

    // Queries
    const { data: runs, isLoading: runsLoading } = useQuery({
        queryKey: ['reconciliation-runs'],
        queryFn: () => reconciliationApi.getRuns(10),
    });

    const { data: discrepancies, isLoading: discLoading } = useQuery({
        queryKey: ['reconciliation-discrepancies'],
        queryFn: () => reconciliationApi.getDiscrepancies(24, false), // Unresolved last 24h
    });

    // Mutations
    const runMutation = useMutation({
        mutationFn: (broker?: string) => reconciliationApi.triggerRun(broker),
        onSuccess: () => {
            toast.success('Reconciliation triggered');
            queryClient.invalidateQueries({ queryKey: ['reconciliation-runs'] });
        },
        onError: (err: any) => toast.error(`Failed to start: ${err.message}`)
    });

    const resolveMutation = useMutation({
        mutationFn: ({ id, action }: { id: number, action: string }) =>
            reconciliationApi.resolveDiscrepancy(id, action),
        onSuccess: () => {
            toast.success('Discrepancy resolved');
            queryClient.invalidateQueries({ queryKey: ['reconciliation-discrepancies'] });
        }
    });

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                    <button
                        onClick={() => setView('discrepancies')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${view === 'discrepancies'
                                ? 'bg-white dark:bg-gray-700 shadow text-blue-600 dark:text-blue-400'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                    >
                        Discrepancies
                        {discrepancies && discrepancies.length > 0 && (
                            <span className="ml-2 bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full text-xs">
                                {discrepancies.length}
                            </span>
                        )}
                    </button>
                    <button
                        onClick={() => setView('history')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${view === 'history'
                                ? 'bg-white dark:bg-gray-700 shadow text-blue-600 dark:text-blue-400'
                                : 'text-gray-500 hover:text-gray-900'
                            }`}
                    >
                        Run History
                    </button>
                </div>

                <button
                    onClick={() => runMutation.mutate(undefined)}
                    disabled={runMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${runMutation.isPending ? 'animate-spin' : ''}`} />
                    Run Reconciliation
                </button>
            </div>

            {view === 'discrepancies' && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    {discLoading ? (
                        <div className="p-8 text-center text-gray-500">Loading discrepancies...</div>
                    ) : discrepancies?.length === 0 ? (
                        <div className="p-12 text-center flex flex-col items-center">
                            <CheckCircle className="w-12 h-12 text-green-500 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white">All Clear</h3>
                            <p className="text-gray-500 mt-1">No position discrepancies found</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                            {discrepancies?.map(disc => (
                                <div key={disc.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                                    <div className="flex justify-between items-start">
                                        <div className="flex gap-4">
                                            <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
                                                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <h4 className="font-bold text-gray-900 dark:text-white">{disc.symbol}</h4>
                                                    <span className="px-2 py-0.5 rounded text-xs font-mono bg-gray-100 dark:bg-gray-700">
                                                        #{disc.id}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                                    Type: <span className="font-medium">{disc.discrepancy_type}</span>
                                                </p>
                                                <div className="mt-2 text-sm grid grid-cols-2 gap-4">
                                                    <div>
                                                        <span className="text-gray-500">Internal:</span>
                                                        <span className="font-mono ml-2">{disc.internal_qty}</span>
                                                    </div>
                                                    <div>
                                                        <span className="text-gray-500">Broker:</span>
                                                        <span className="font-mono ml-2">{disc.broker_qty}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex flex-col gap-2">
                                            <button
                                                onClick={() => resolveMutation.mutate({ id: disc.id, action: 'SYNC_FROM_BROKER' })}
                                                className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded hover:bg-blue-100"
                                            >
                                                Sync from Broker
                                            </button>
                                            <button
                                                onClick={() => resolveMutation.mutate({ id: disc.id, action: 'IGNORE' })}
                                                className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded hover:bg-gray-100"
                                            >
                                                Ignore
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {view === 'history' && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Run ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Discrepancies</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {runs?.map(run => (
                                <tr key={run.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                                        #{run.id}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                        {format(new Date(run.started_at), 'MMM d, HH:mm:ss')}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${run.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                                                run.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                                    'bg-yellow-100 text-yellow-800'
                                            }`}>
                                            {run.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {run.discrepancies_found > 0 ? (
                                            <span className="text-red-500 font-bold">{run.discrepancies_found} Found</span>
                                        ) : (
                                            <span className="text-green-500">None</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
