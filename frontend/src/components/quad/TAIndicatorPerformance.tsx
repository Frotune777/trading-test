'use client';

import { useQuery } from '@tanstack/react-query';
import { taApi, type TAPerformance } from '@/lib/api/ta';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { useState } from 'react';

const CATEGORY_COLORS: Record<string, string> = {
    trend: '#3B82F6',      // blue
    momentum: '#10B981',   // green
    volatility: '#F59E0B', // orange
    volume: '#8B5CF6',     // purple
};

export default function TAIndicatorPerformance() {
    const [selectedRegime, setSelectedRegime] = useState<string>('all');

    const { data, isLoading, error } = useQuery<TAPerformance[]>({
        queryKey: ['ta-performance'],
        queryFn: () => taApi.getPerformance(),
        refetchInterval: 60000,
    });

    if (isLoading) {
        return (
            <div className="w-full h-96 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Loading performance data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-96 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <p className="text-red-600 dark:text-red-400">Failed to load performance data</p>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="w-full h-96 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">No performance data available</p>
            </div>
        );
    }

    // Filter by regime if selected
    const filteredData = selectedRegime === 'all'
        ? data
        : data.filter(item => item.regime === selectedRegime);

    // Aggregate by category if showing all regimes
    const chartData = selectedRegime === 'all'
        ? Object.entries(
            filteredData.reduce((acc, item) => {
                if (!acc[item.category]) {
                    acc[item.category] = { category: item.category, accuracy: 0, signals: 0, count: 0 };
                }
                acc[item.category].accuracy += item.accuracy;
                acc[item.category].signals += item.signals;
                acc[item.category].count += 1;
                return acc;
            }, {} as Record<string, { category: string; accuracy: number; signals: number; count: number }>)
        ).map(([_, value]) => ({
            category: value.category,
            accuracy: (value.accuracy / value.count) * 100,
            signals: value.signals,
        }))
        : filteredData.map(item => ({
            category: item.category,
            accuracy: item.accuracy * 100,
            signals: item.signals,
        }));

    // Get unique regimes for filter
    const regimes = ['all', ...new Set(data.map(item => item.regime))];

    return (
        <div className="w-full space-y-4">
            {/* Header with Filter */}
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Indicator Performance by Category
                </h3>
                <select
                    value={selectedRegime}
                    onChange={(e) => setSelectedRegime(e.target.value)}
                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                >
                    {regimes.map(regime => (
                        <option key={regime} value={regime}>
                            {regime === 'all' ? 'All Regimes' : regime}
                        </option>
                    ))}
                </select>
            </div>

            {/* Chart */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="category"
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
                            formatter={(value: number, name: string, props: any) => {
                                if (name === 'accuracy') {
                                    return [`${value.toFixed(1)}%`, 'Accuracy'];
                                }
                                return [value, 'Signals'];
                            }}
                        />
                        <Legend />
                        <Bar dataKey="accuracy" name="Accuracy">
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.category] || '#6B7280'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {chartData.map((item) => (
                    <div key={item.category} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                        <div className="flex items-center gap-2 mb-2">
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: CATEGORY_COLORS[item.category] || '#6B7280' }}
                            />
                            <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                                {item.category}
                            </p>
                        </div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                            {item.accuracy.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{item.signals} signals</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
