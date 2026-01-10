'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { feedHealthApi } from '@/lib/api/feed-health';
import {
    Activity, Zap, Clock, AlertTriangle,
    RotateCcw, Play, Square, CheckCircle2, Wifi
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function DataHealthDashboard() {
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ['feed-health-metrics'],
        queryFn: feedHealthApi.getMetrics,
        refetchInterval: 2000,
    });

    const resetMutation = useMutation({
        mutationFn: feedHealthApi.resetCircuitBreaker,
        onSuccess: () => {
            toast.success('Circuit breaker reset');
            queryClient.invalidateQueries({ queryKey: ['feed-health-metrics'] });
        },
        onError: () => toast.error('Failed to reset circuit breaker')
    });

    const startMutation = useMutation({
        mutationFn: feedHealthApi.startMonitor,
        onSuccess: () => toast.success('Feed monitor started')
    });

    const stopMutation = useMutation({
        mutationFn: feedHealthApi.stopMonitor,
        onSuccess: () => toast.success('Feed monitor stopped')
    });

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-48 bg-gray-100 dark:bg-gray-800 rounded-lg" />
                ))}
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex justify-end gap-2">
                {data.metrics.pipeline.circuit_breaker_active && (
                    <button
                        onClick={() => resetMutation.mutate()}
                        className="px-4 py-2 bg-yellow-100 text-yellow-700 hover:bg-yellow-200 rounded-lg flex items-center gap-2 font-medium"
                    >
                        <RotateCcw className="w-4 h-4" />
                        Reset Circuit Breaker
                    </button>
                )}
                <button
                    onClick={() => startMutation.mutate()}
                    className="px-4 py-2 bg-green-100 text-green-700 hover:bg-green-200 rounded-lg flex items-center gap-2 font-medium"
                >
                    <Play className="w-4 h-4" />
                    Start Monitor
                </button>
                <button
                    onClick={() => stopMutation.mutate()}
                    className="px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 rounded-lg flex items-center gap-2 font-medium"
                >
                    <Square className="w-4 h-4" />
                    Stop Monitor
                </button>
            </div>

            {/* Main Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Overall Status */}
                <div className={`p-4 rounded-xl border flex items-center justify-between ${data.overall_status === 'HEALTHY'
                        ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
                        : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                    }`}>
                    <div>
                        <p className="text-sm font-medium opacity-80">Feed Status</p>
                        <p className="text-2xl font-bold">{data.overall_status}</p>
                    </div>
                    <Wifi className={`w-8 h-8 ${data.overall_status === 'HEALTHY' ? 'text-green-500' : 'text-red-500'
                        }`} />
                </div>

                {/* Latency */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Avg Latency</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                {data.metrics.average_latency.toFixed(1)}ms
                            </p>
                        </div>
                        <Activity className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                        Target: &lt;100ms
                    </div>
                </div>

                {/* Active/Stale */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Active Symbols</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                {data.metrics.active_symbols}
                            </p>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded ${data.metrics.stale_symbols > 0 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
                                }`}>
                                {data.metrics.stale_symbols} Stale
                            </span>
                        </div>
                    </div>
                </div>

                {/* Circuit Breaker Status */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Pipeline Health</p>
                            <p className={`text-lg font-bold ${data.metrics.pipeline.circuit_breaker_active ? 'text-red-600' : 'text-green-600'
                                }`}>
                                {data.metrics.pipeline.circuit_breaker_active ? 'BREAKER TRIPPED' : 'OPERATIONAL'}
                            </p>
                        </div>
                        <Zap className={`w-5 h-5 ${data.metrics.pipeline.circuit_breaker_active ? 'text-red-500' : 'text-green-500'
                            }`} />
                    </div>
                    {data.metrics.pipeline.circuit_breaker_active && (
                        <p className="text-xs text-red-500 mt-1">
                            Data flow halted due to errors
                        </p>
                    )}
                </div>
            </div>

            {/* Component Details */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Component Status</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(data.components).map(([name, isHealthy]) => (
                        <div key={name} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                            <span className="capitalize font-medium text-gray-700 dark:text-gray-300">{name}</span>
                            {isHealthy ? (
                                <div className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
                                    <CheckCircle2 className="w-4 h-4" />
                                    OK
                                </div>
                            ) : (
                                <div className="flex items-center gap-1.5 text-red-600 text-sm font-medium">
                                    <AlertTriangle className="w-4 h-4" />
                                    ERROR
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
