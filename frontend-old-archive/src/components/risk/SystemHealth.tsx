'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api/client';
import { Database, Server, Activity, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function SystemHealth() {
    const { data: health, isLoading } = useQuery({
        queryKey: ['system-health'],
        queryFn: async () => {
            const dbRes = await api.get('/health/system');
            const wsRes = await api.get('/health/openalgo');
            return {
                ...dbRes.data,
                openalgo: wsRes.data
            };
        },
        refetchInterval: 10000,
    });

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-32 bg-gray-100 dark:bg-gray-800 rounded-lg" />
                ))}
            </div>
        );
    }

    const getStatusIcon = (status: string) => {
        if (status === 'connected' || status === 'healthy') {
            return <CheckCircle2 className="w-6 h-6 text-green-500" />;
        }
        if (status === 'unavailable' || status === 'degraded') {
            return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
        }
        return <XCircle className="w-6 h-6 text-red-500" />;
    };

    const StatusCard = ({ title, status, icon: Icon, details }: any) => (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <Icon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
                </div>
                {getStatusIcon(status)}
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Status</span>
                    <span className={`font-medium uppercase ${status === 'connected' || status === 'healthy' ? 'text-green-600 dark:text-green-400' :
                            status === 'unavailable' ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                        }`}>
                        {status}
                    </span>
                </div>
                {details && (
                    <div className="text-xs text-gray-400 font-mono mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                        {JSON.stringify(details, null, 2)}
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Activity className="w-6 h-6 text-blue-600" />
                System Health Status
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatusCard
                    title="Database"
                    status={health?.database}
                    icon={Database}
                />
                <StatusCard
                    title="Redis / Cache"
                    status={health?.redis}
                    icon={Server}
                />
                <StatusCard
                    title="OpenAlgo Feed"
                    status={health?.openalgo?.status}
                    icon={Activity}
                    details={health?.openalgo?.details}
                />
            </div>
        </div>
    );
}
