'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Cell, LineChart, Line, Legend
} from 'recharts';

interface TAAccuracyChartProps {
    accuracy: any;
    performance: any[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const TAAccuracyChart: React.FC<TAAccuracyChartProps> = ({ accuracy, performance }) => {
    // Format performance data for bar chart
    const barData = performance.map(p => ({
        name: p.category.charAt(0).toUpperCase() + p.category.slice(1),
        accuracy: p.accuracy * 100
    }));

    // Mock trend data for visualization (in a real app this would come from the API)
    const trendData = [
        { date: 'Day 1', accuracy: 55 },
        { date: 'Day 5', accuracy: 58 },
        { date: 'Day 10', accuracy: 62 },
        { date: 'Day 15', accuracy: 60 },
        { date: 'Day 20', accuracy: 65 },
        { date: 'Day 25', accuracy: 63 },
        { date: 'Day 30', accuracy: 67 },
    ];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Accuracy by Category */}
            <Card className="bg-slate-950 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-sm font-medium">Indicator Group Performance</CardTitle>
                    <CardDescription>Winning rate per technical category (Last 30 days)</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={barData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis
                                    dataKey="name"
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(v) => `${v}%`}
                                    domain={[0, 100]}
                                />
                                <Tooltip
                                    cursor={{ fill: '#1e293b' }}
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Bar dataKey="accuracy" radius={[4, 4, 0, 0]}>
                                    {barData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Accuracy Trend */}
            <Card className="bg-slate-950 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-sm font-medium">Accuracy Trend</CardTitle>
                    <CardDescription>Composite signal accuracy over time</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(v) => `${v}%`}
                                    domain={[40, 80]}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}
                                    itemStyle={{ color: '#60a5fa' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="accuracy"
                                    stroke="#3b82f6"
                                    strokeWidth={3}
                                    dot={{ r: 4, fill: '#3b82f6', strokeWidth: 0 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Accuracy Tip */}
            <Card className="col-span-1 lg:col-span-2 bg-blue-500/5 border-blue-500/20">
                <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <TargetIcon className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="space-y-1">
                            <h4 className="font-bold text-blue-400">Optimization Insight</h4>
                            <p className="text-sm text-slate-300 leading-relaxed">
                                The TA Aggregator currently performs best in <strong>{accuracy?.best_regime?.replace('_', ' ')}</strong> conditions.
                                Consider increasing the weight of <strong>trend</strong> indicators when your accuracy trend is above 60%
                                to capture longer movements.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

const TargetIcon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="12" r="2" fill="currentColor" />
    </svg>
);

export default TAAccuracyChart;
