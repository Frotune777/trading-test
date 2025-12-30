'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { riskApi, Alert } from '@/lib/api/risk';
import { AlertTriangle, Info, CheckCircle2, XCircle, Bell } from 'lucide-react';
import toast from 'react-hot-toast';

interface AlertListProps {
    alerts: Alert[];
}

export default function AlertList({ alerts }: AlertListProps) {
    const queryClient = useQueryClient();

    const acknowledgeMutation = useMutation({
        mutationFn: riskApi.acknowledgeAlert,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['risk-dashboard'] });
            toast.success('Alert acknowledged');
        },
        onError: () => {
            toast.error('Failed to acknowledge alert');
        }
    });

    const getAlertIcon = (type: string) => {
        switch (type) {
            case 'CRITICAL': return <XCircle className="w-5 h-5 text-red-500" />;
            case 'WARNING': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    const getAlertStyle = (type: string) => {
        switch (type) {
            case 'CRITICAL': return 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30';
            case 'WARNING': return 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-900/30';
            default: return 'bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-900/30';
        }
    };

    const activeAlerts = alerts.filter(a => !a.acknowledged);
    const acknowledgedAlerts = alerts.filter(a => a.acknowledged);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    <Bell className="w-5 h-5 text-blue-600" />
                    System Alerts
                    {activeAlerts.length > 0 && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-xs">
                            {activeAlerts.length} Active
                        </span>
                    )}
                </h2>
            </div>

            <div className="space-y-3">
                {activeAlerts.length === 0 ? (
                    <div className="py-8 text-center text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg border border-dashed border-gray-200 dark:border-gray-700">
                        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-500 opacity-50" />
                        <p>No active alerts</p>
                    </div>
                ) : (
                    activeAlerts.map(alert => (
                        <div
                            key={alert.id}
                            className={`p-4 rounded-lg border flex items-start gap-4 transition-all hover:shadow-sm ${getAlertStyle(alert.alert_type)}`}
                        >
                            <div className="flex-shrink-0 mt-0.5">
                                {getAlertIcon(alert.alert_type)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${alert.alert_type === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                                            alert.alert_type === 'WARNING' ? 'bg-yellow-100 text-yellow-700' :
                                                'bg-blue-100 text-blue-700'
                                        }`}>
                                        {alert.alert_type}
                                    </span>
                                    <span className="text-xs text-gray-500 font-medium">
                                        {alert.category}
                                    </span>
                                    <span className="text-xs text-gray-400">
                                        • {new Date(alert.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                                    {alert.title}
                                </h3>
                                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                                    {alert.message}
                                </p>
                                {alert.related_symbol && (
                                    <p className="text-xs font-medium text-gray-500 mt-2">
                                        Symbol: {alert.related_symbol}
                                    </p>
                                )}
                            </div>
                            <div className="flex-shrink-0">
                                <button
                                    onClick={() => acknowledgeMutation.mutate(alert.id)}
                                    disabled={acknowledgeMutation.isPending}
                                    className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors shadow-sm"
                                >
                                    Acknowledge
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {acknowledgedAlerts.length > 0 && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
                        Show {acknowledgedAlerts.length} acknowledged alerts
                    </button>
                </div>
            )}
        </div>
    );
}
