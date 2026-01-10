'use client';

import { useQuery } from '@tanstack/react-query';
import { decisionApi, type TimelinePoint } from '@/lib/api/decisions';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Scatter, ScatterChart, ZAxis } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface DecisionTimelineProps {
    symbol: string;
    days?: number;
}

export default function DecisionTimeline({ symbol, days = 30 }: DecisionTimelineProps) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['decision-timeline', symbol, days],
        queryFn: () => decisionApi.getTimeline(symbol, days),
        refetchInterval: 30000,
    });

    if (isLoading) {
        return (
            <div className="w-full h-96 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Loading decision timeline...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-96 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <p className="text-red-600 dark:text-red-400">Failed to load timeline</p>
            </div>
        );
    }

    if (!data || data.timeline.length === 0) {
        return (
            <div className="w-full h-96 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">No decisions found for {symbol}</p>
            </div>
        );
    }

    // Transform timeline data for charts
    const chartData = data.timeline.map((point, i) => ({
        index: i,
        timestamp: new Date(point.timestamp).getTime(),
        date: new Date(point.timestamp).toLocaleDateString(),
        time: new Date(point.timestamp).toLocaleTimeString(),
        conviction: point.conviction,
        price: point.price || 0,
        decision: point.decision,
        regime: point.regime,
        executed: point.executed,
        pnl: point.pnl || 0,
        // For scatter plot
        decisionValue: point.decision === 'BUY' ? 1 : point.decision === 'SELL' ? -1 : 0,
    }));

    const getDecisionColor = (decision: string) => {
        switch (decision) {
            case 'BUY': return '#10B981';  // green
            case 'SELL': return '#EF4444'; // red
            default: return '#6B7280';     // gray
        }
    };

    const getDecisionIcon = (decision: string) => {
        switch (decision) {
            case 'BUY': return <TrendingUp className="w-3 h-3" />;
            case 'SELL': return <TrendingDown className="w-3 h-3" />;
            default: return <Minus className="w-3 h-3" />;
        }
    };

    // Calculate stats
    const buyCount = data.timeline.filter(p => p.decision === 'BUY').length;
    const sellCount = data.timeline.filter(p => p.decision === 'SELL').length;
    const holdCount = data.timeline.filter(p => p.decision === 'HOLD').length;
    const avgConviction = data.timeline.reduce((sum, p) => sum + p.conviction, 0) / data.timeline.length;
    const executedCount = data.timeline.filter(p => p.executed).length;

    return (
        <div className="w-full space-y-6">
            {/* Stats Summary */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Total Decisions</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {data.timeline.length}
                    </p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg shadow">
                    <p className="text-sm text-green-700 dark:text-green-400">BUY Signals</p>
                    <p className="text-2xl font-bold text-green-600">{buyCount}</p>
                </div>
                <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg shadow">
                    <p className="text-sm text-red-700 dark:text-red-400">SELL Signals</p>
                    <p className="text-2xl font-bold text-red-600">{sellCount}</p>
                </div>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">HOLD Signals</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{holdCount}</p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg shadow">
                    <p className="text-sm text-blue-700 dark:text-blue-400">Avg Conviction</p>
                    <p className="text-2xl font-bold text-blue-600">{avgConviction.toFixed(0)}</p>
                </div>
            </div>

            {/* Conviction Over Time */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Conviction Evolution
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="date"
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                        />
                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF' }}
                            domain={[0, 100]}
                            label={{ value: 'Conviction', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '0.5rem'
                            }}
                            labelStyle={{ color: '#F3F4F6' }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="conviction"
                            stroke="#3B82F6"
                            strokeWidth={2}
                            dot={{ fill: '#3B82F6', r: 4 }}
                            activeDot={{ r: 6 }}
                            name="Conviction"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Decision Points */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Decision Points
                </h3>
                <div className="space-y-2">
                    {data.timeline.map((point, i) => (
                        <div
                            key={i}
                            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                        >
                            <div className="flex-shrink-0">
                                <div
                                    className={`flex items-center justify-center w-8 h-8 rounded-full`}
                                    style={{ backgroundColor: getDecisionColor(point.decision) + '20' }}
                                >
                                    <span style={{ color: getDecisionColor(point.decision) }}>
                                        {getDecisionIcon(point.decision)}
                                    </span>
                                </div>
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="font-semibold text-gray-900 dark:text-white">
                                        {point.decision}
                                    </span>
                                    {point.executed && (
                                        <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                            Executed
                                        </span>
                                    )}
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                    {new Date(point.timestamp).toLocaleString()} • {point.regime}
                                </p>
                            </div>

                            <div className="flex-shrink-0 text-right">
                                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                    Conviction: {point.conviction}
                                </p>
                                {point.price && (
                                    <p className="text-xs text-gray-600 dark:text-gray-400">
                                        ₹{point.price.toFixed(2)}
                                    </p>
                                )}
                                {point.pnl !== undefined && point.pnl !== 0 && (
                                    <p className={`text-xs font-medium ${point.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {point.pnl >= 0 ? '+' : ''}₹{point.pnl.toFixed(2)}
                                    </p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
