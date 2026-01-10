'use client';

import { useQuery } from '@tanstack/react-query';
import { riskApi } from '@/lib/api/risk';
import {
    Shield,
    AlertTriangle,
    TrendingUp,
    TrendingDown,
    DollarSign,
    Activity,
    PieChart as PieChartIcon
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
    Legend
} from 'recharts';

export default function RiskDashboard() {
    const { data, isLoading } = useQuery({
        queryKey: ['risk-dashboard'],
        queryFn: riskApi.getDashboard,
        refetchInterval: 5000,
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

    if (!data) return null;

    const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

    const concentrationData = Object.entries(data.concentration_by_symbol).map(([name, value]) => ({
        name,
        value
    }));

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(val);
    };

    const getUtilizationColor = (pct: number) => {
        if (pct >= 90) return 'bg-red-500';
        if (pct >= 75) return 'bg-yellow-500';
        return 'bg-blue-500';
    };

    return (
        <div className="space-y-6">
            {/* Top Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Total P&L */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-gray-500 font-medium">Total P&L</p>
                        <DollarSign className={`w-4 h-4 ${data.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`} />
                    </div>
                    <p className={`text-2xl font-bold ${data.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(data.total_pnl)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Realized + Unrealized</p>
                </div>

                {/* Daily P&L */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-gray-500 font-medium">Daily P&L</p>
                        <Activity className="w-4 h-4 text-blue-500" />
                    </div>
                    <p className={`text-2xl font-bold ${data.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(data.daily_pnl)}
                    </p>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2 dark:bg-gray-700">
                        <div
                            className={`h-1.5 rounded-full ${getUtilizationColor(data.utilization.daily_loss_limit)}`}
                            style={{ width: `${Math.min(data.utilization.daily_loss_limit, 100)}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                        {data.utilization.daily_loss_limit.toFixed(1)}% of loss limit
                    </p>
                </div>

                {/* Exposure */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-gray-500 font-medium">Total Exposure</p>
                        <Shield className="w-4 h-4 text-purple-500" />
                    </div>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {formatCurrency(data.total_exposure)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                        across {data.position_count} positions
                    </p>
                </div>

                {/* Drawdown */}
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-gray-500 font-medium">Drawdown</p>
                        <TrendingDown className="w-4 h-4 text-orange-500" />
                    </div>
                    <p className="text-2xl font-bold text-orange-600">
                        {data.current_drawdown_pct.toFixed(2)}%
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                        Max limit: {data.limits.max_drawdown_pct}%
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Limit Utilization */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-blue-500" />
                        Risk Limit Utilization
                    </h3>

                    <div className="space-y-4">
                        {/* Position Count */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600 dark:text-gray-400">Position Count</span>
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {data.position_count} / {data.limits.max_positions}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                                <div
                                    className={`h-2 rounded-full ${getUtilizationColor(data.utilization.position_limit)}`}
                                    style={{ width: `${data.utilization.position_limit}%` }}
                                />
                            </div>
                        </div>

                        {/* Daily Loss */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600 dark:text-gray-400">Daily Loss Limit</span>
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {formatCurrency(Math.abs(Math.min(0, data.daily_pnl)))} / {formatCurrency(data.limits.max_daily_loss)}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                                <div
                                    className={`h-2 rounded-full ${getUtilizationColor(data.utilization.daily_loss_limit)}`}
                                    style={{ width: `${Math.min(100, data.utilization.daily_loss_limit)}%` }}
                                />
                            </div>
                        </div>

                        {/* Weekly Loss */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600 dark:text-gray-400">Weekly Loss Limit</span>
                                <span className="font-medium text-gray-900 dark:text-white">
                                    {formatCurrency(Math.abs(Math.min(0, data.weekly_pnl)))} / {formatCurrency(data.limits.max_weekly_loss)}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                                <div
                                    className={`h-2 rounded-full ${getUtilizationColor(data.utilization.weekly_loss_limit)}`}
                                    style={{ width: `${Math.min(100, data.utilization.weekly_loss_limit)}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Concentration Chart */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <PieChartIcon className="w-5 h-5 text-purple-500" />
                        Symbol Concentration
                    </h3>

                    <div className="h-64">
                        {concentrationData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={concentrationData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {concentrationData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        formatter={(value: number) => `${value.toFixed(1)}%`}
                                        contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                                    />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">
                                No active positions
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
