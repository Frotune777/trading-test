'use client';

import { useQuery } from '@tanstack/react-query';
import { taApi, type TAAccuracy } from '@/lib/api/ta';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface TAAccuracyChartProps {
    days?: number;
}

export default function TAAccuracyChart({ days = 30 }: TAAccuracyChartProps) {
    const { data, isLoading, error } = useQuery<TAAccuracy>({
        queryKey: ['ta-accuracy', days],
        queryFn: () => taApi.getAccuracy(days),
        refetchInterval: 60000, // Refetch every minute
    });

    if (isLoading) {
        return (
            <div className="w-full h-64 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Loading accuracy data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-64 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <p className="text-red-600 dark:text-red-400">Failed to load accuracy data</p>
            </div>
        );
    }

    if (!data) return null;

    const accuracyPercentage = (data.overall_accuracy * 100).toFixed(1);
    const accuracyColor = data.overall_accuracy >= 0.6 ? 'text-green-600' : data.overall_accuracy >= 0.5 ? 'text-yellow-600' : 'text-red-600';

    // Transform regime breakdown for chart
    const chartData = Object.entries(data.regime_breakdown || {}).map(([regime, accuracy]) => ({
        regime,
        accuracy: accuracy * 100,
    }));

    return (
        <div className="w-full space-y-4">
            {/* Header Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Overall Accuracy</p>
                    <p className={`text-3xl font-bold ${accuracyColor}`}>{accuracyPercentage}%</p>
                    <p className="text-xs text-gray-500 mt-1">{data.sample_size} signals</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Best Regime</p>
                    <div className="flex items-center gap-2 mt-2">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                            {data.best_regime}
                        </p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        {((data.regime_breakdown?.[data.best_regime] || 0) * 100).toFixed(1)}% accuracy
                    </p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Worst Regime</p>
                    <div className="flex items-center gap-2 mt-2">
                        <TrendingDown className="w-5 h-5 text-red-600" />
                        <p className="text-lg font-semibold text-gray-900 dark:text-white">
                            {data.worst_regime}
                        </p>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        {((data.regime_breakdown?.[data.worst_regime] || 0) * 100).toFixed(1)}% accuracy
                    </p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Sample Period</p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white">{days}</p>
                    <p className="text-xs text-gray-500 mt-1">days</p>
                </div>
            </div>

            {/* Chart */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Accuracy by Regime
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="regime"
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF' }}
                        />
                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF' }}
                            domain={[0, 100]}
                            label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '0.5rem'
                            }}
                            labelStyle={{ color: '#F3F4F6' }}
                            formatter={(value: number) => [`${value.toFixed(1)}%`, 'Accuracy']}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="accuracy"
                            stroke="#10B981"
                            strokeWidth={2}
                            dot={{ fill: '#10B981', r: 4 }}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
