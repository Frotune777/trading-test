'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { Brain, Target, TrendingUp, AlertCircle, BarChart3 } from 'lucide-react';

export default function MLModelMetrics({ symbol }: { symbol: string }) {
    const { data: metrics, isLoading } = useQuery({
        queryKey: ['ml-accuracy', symbol],
        queryFn: () => analyticsApi.getAccuracy(symbol),
        enabled: !!symbol,
    });

    if (isLoading) {
        return <div className="h-64 bg-gray-50 dark:bg-gray-800 rounded-xl animate-pulse" />;
    }

    if (!metrics) return null;

    const pieData = [
        { name: 'Correct', value: metrics.correct_signals },
        { name: 'Incorrect', value: metrics.total_signals - metrics.correct_signals },
    ];

    const COLORS = ['#10B981', '#EF4444'];

    const rollingData = Object.entries(metrics.rolling_win_rates || {}).map(([date, rate]) => ({
        date: date.split('T')[0],
        rate: rate * 100,
    })).sort((a, b) => a.date.localeCompare(b.date));

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-600" />
                    <h3 className="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-sm">Model Performance & Accuracy</h3>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-100 dark:border-purple-800">
                    <Target className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                    <span className="text-xs font-black text-purple-700 dark:text-purple-300">
                        WIN RATE: {(metrics.win_rate * 100).toFixed(1)}%
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: Win Rate Pie */}
                <div className="flex flex-col items-center justify-center">
                    <div className="h-[180px] w-full relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#FFF' }}
                                    itemStyle={{ color: '#FFF' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-2xl font-black text-gray-900 dark:text-white">
                                {metrics.total_signals}
                            </span>
                            <span className="text-[10px] text-gray-400 uppercase font-black">Total Signals</span>
                        </div>
                    </div>
                    <div className="flex gap-4 mt-2">
                        <div className="flex items-center gap-1.5">
                            <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                            <span className="text-xs font-bold text-gray-500">Correct: {metrics.correct_signals}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                            <span className="text-xs font-bold text-gray-500">Missed: {metrics.total_signals - metrics.correct_signals}</span>
                        </div>
                    </div>
                </div>

                {/* Center: Rolling Win Rate Chart */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="h-[180px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={rollingData}>
                                <defs>
                                    <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis
                                    dataKey="date"
                                    fontSize={9}
                                    tickMargin={10}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <YAxis
                                    fontSize={9}
                                    axisLine={false}
                                    tickLine={false}
                                    domain={[0, 100]}
                                    unit="%"
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#FFF' }}
                                    itemStyle={{ color: '#FFF' }}
                                />
                                <Area type="monotone" dataKey="rate" stroke="#8B5CF6" fillOpacity={1} fill="url(#colorRate)" strokeWidth={3} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                    <p className="text-[10px] text-gray-400 text-center uppercase font-bold tracking-widest">Rolling Win Rate (30-Day Window)</p>
                </div>
            </div>

            {/* Accuracy Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8 pt-8 border-t border-gray-100 dark:border-gray-700">
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900/40">
                    <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Win Conviction</p>
                    <p className="text-lg font-black text-green-600">{Math.round(metrics.avg_conviction_winning)}</p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900/40">
                    <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Loss Conviction</p>
                    <p className="text-lg font-black text-red-600">{Math.round(metrics.avg_conviction_losing)}</p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900/40">
                    <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Expectancy</p>
                    <p className="text-lg font-black text-blue-600">
                        {((metrics.win_rate * metrics.avg_conviction_winning) / 100).toFixed(2)}
                    </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900/40">
                    <p className="text-[10px] text-gray-500 uppercase font-black mb-1">Total PnL</p>
                    <p className={`text-lg font-black ${metrics.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {metrics.total_profit_loss >= 0 ? '+' : ''}{metrics.total_profit_loss.toFixed(1)}%
                    </p>
                </div>
            </div>
        </div>
    );
}
