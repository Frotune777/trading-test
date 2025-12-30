'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { riskApi } from '@/lib/api/risk';
import RiskDashboard from '@/components/risk/RiskDashboard';
import KillSwitch from '@/components/risk/KillSwitch';
import RiskLimitsConfig from '@/components/risk/RiskLimitsConfig';
import AlertList from '@/components/risk/AlertList';
import SystemHealth from '@/components/risk/SystemHealth';
import DataHealthDashboard from '@/components/risk/DataHealthDashboard';
import ReconciliationDashboard from '@/components/risk/ReconciliationDashboard';
import {
    Shield, Settings, Bell, LayoutDashboard, Activity,
    Wifi, RefreshCw
} from 'lucide-react';

export default function RiskPage() {
    const [activeTab, setActiveTab] = useState('overview');

    const { data, isLoading } = useQuery({
        queryKey: ['risk-dashboard'],
        queryFn: riskApi.getDashboard,
        refetchInterval: 5000,
    });

    const tabs = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'limits', label: 'Limits Config', icon: Settings },
        { id: 'alerts', label: 'Alerts', icon: Bell },
        { id: 'system', label: 'System', icon: Activity },
        { id: 'data', label: 'Data Health', icon: Wifi },
        { id: 'reconciliation', label: 'Reconciliation', icon: RefreshCw },
    ];

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-8" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-64 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="container mx-auto px-4 py-8 space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Shield className="w-8 h-8 text-blue-600" />
                        Risk Command Center
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        Real-time risk monitoring, limit enforcement, and emergency controls
                    </p>
                </div>

                {/* Global Status Badge */}
                <div className={`px-4 py-2 rounded-lg border flex items-center gap-2 ${data.kill_switch.enabled
                    ? 'bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400'
                    : 'bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400'
                    }`}>
                    <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${data.kill_switch.enabled ? 'bg-red-500' : 'bg-green-500'
                        }`} />
                    <span className="font-semibold">
                        {data.kill_switch.enabled ? 'SYSTEM HALTED' : 'SYSTEM HEALTHY'}
                    </span>
                </div>
            </div>

            {/* Kill Switch (Always Visible if Active) */}
            <KillSwitch status={data.kill_switch} />

            {/* Tabs */}
            <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap
              ${activeTab === tab.id
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                            }
            `}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                        {tab.id === 'alerts' && data.alerts.some(a => !a.acknowledged) && (
                            <span className="px-1.5 py-0.5 bg-red-100 text-red-600 rounded-full text-xs">
                                {data.alerts.filter(a => !a.acknowledged).length}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                {activeTab === 'overview' && (
                    <RiskDashboard />
                )}

                {activeTab === 'limits' && (
                    <RiskLimitsConfig initialLimits={data.limits} />
                )}

                {activeTab === 'alerts' && (
                    <AlertList alerts={data.alerts} />
                )}

                {activeTab === 'system' && (
                    <SystemHealth />
                )}

                {activeTab === 'data' && (
                    <DataHealthDashboard />
                )}

                {activeTab === 'reconciliation' && (
                    <ReconciliationDashboard />
                )}
            </div>
        </div>
    );
}
