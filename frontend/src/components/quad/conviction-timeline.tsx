"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { TrendingUp, Activity, Target, AlertCircle } from 'lucide-react';
import { QuadService, getBiasColorClass } from '@/lib/api/quad';
import type { ConvictionTimeline as ConvictionTimelineType } from '@/lib/api/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { format } from 'date-fns';

interface Props {
    symbol: string;
    days?: number;
}

export default function ConvictionTimeline({ symbol, days = 30 }: Props) {
    const [timeline, setTimeline] = useState<ConvictionTimelineType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTimeline = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await QuadService.getConvictionTimeline(symbol, days);
                setTimeline(data);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Failed to fetch conviction timeline');
                console.error('Error fetching conviction timeline:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchTimeline();
    }, [symbol, days]);

    if (loading) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="text-blue-400 w-5 h-5 animate-pulse" />
                        Conviction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-slate-400">Loading timeline...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !timeline) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="text-blue-400 w-5 h-5" />
                        Conviction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-400">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{error || 'No timeline data available'}</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Prepare chart data
    const chartData = timeline.data_points.map(point => ({
        timestamp: new Date(point.timestamp).getTime(),
        conviction: point.conviction_score,
        bias: point.bias,
        label: format(new Date(point.timestamp), 'MMM dd HH:mm'),
    }));

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-slate-800 border border-slate-700 p-3 rounded shadow-lg">
                    <div className="text-xs text-slate-400 mb-1">{data.label}</div>
                    <div className="text-sm font-mono text-slate-200">
                        Conviction: {data.conviction.toFixed(1)}%
                    </div>
                    <div className={`text-sm ${getBiasColorClass(data.bias)}`}>
                        {data.bias}
                    </div>
                </div>
            );
        }
        return null;
    };

    // Get line color based on recent bias
    const getLineColor = () => {
        switch (timeline.recent_bias.toUpperCase()) {
            case 'BULLISH': return '#4ade80';
            case 'BEARISH': return '#f87171';
            default: return '#94a3b8';
        }
    };

    return (
        <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Activity className="text-blue-400 w-5 h-5" />
                    Conviction Timeline ({days} days)
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Chart */}
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis 
                                dataKey="label" 
                                stroke="#64748b"
                                tick={{ fill: '#64748b', fontSize: 10 }}
                                angle={-45}
                                textAnchor="end"
                                height={60}
                            />
                            <YAxis 
                                domain={[0, 100]}
                                stroke="#64748b"
                                tick={{ fill: '#64748b', fontSize: 12 }}
                                label={{ value: 'Conviction %', angle: -90, position: 'insideLeft', fill: '#64748b' }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine y={50} stroke="#475569" strokeDasharray="3 3" />
                            <Line 
                                type="monotone" 
                                dataKey="conviction" 
                                stroke={getLineColor()}
                                strokeWidth={2}
                                dot={{ fill: getLineColor(), r: 4 }}
                                activeDot={{ r: 6 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
                    {/* Average Conviction */}
                    <div>
                        <div className="text-xs text-slate-500 mb-1">Avg Conviction</div>
                        <div className="text-lg font-mono text-slate-200">
                            {timeline.average_conviction.toFixed(1)}%
                        </div>
                    </div>

                    {/* Volatility */}
                    <div>
                        <div className="text-xs text-slate-500 mb-1">Volatility</div>
                        <div className={`text-lg font-mono ${
                            timeline.conviction_volatility < 10 ? 'text-green-400' :
                            timeline.conviction_volatility < 20 ? 'text-yellow-400' :
                            'text-red-400'
                        }`}>
                            {timeline.conviction_volatility.toFixed(1)}
                        </div>
                    </div>

                    {/* Bias Consistency */}
                    <div>
                        <div className="text-xs text-slate-500 mb-1">Consistency</div>
                        <div className={`text-lg font-mono ${
                            timeline.bias_consistency >= 80 ? 'text-green-400' :
                            timeline.bias_consistency >= 60 ? 'text-yellow-400' :
                            'text-red-400'
                        }`}>
                            {timeline.bias_consistency.toFixed(0)}%
                        </div>
                    </div>

                    {/* Recent Bias Streak */}
                    <div>
                        <div className="text-xs text-slate-500 mb-1">Streak</div>
                        <div className={`text-lg font-mono ${getBiasColorClass(timeline.recent_bias)}`}>
                            {timeline.bias_streak_count}x {timeline.recent_bias.slice(0, 3)}
                        </div>
                    </div>
                </div>

                {/* Trend Indicator */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <span className="text-xs text-slate-500">Conviction Trend</span>
                    <span className={`flex items-center gap-1 text-sm font-medium ${
                        timeline.conviction_trend === 'INCREASING' ? 'text-green-400' :
                        timeline.conviction_trend === 'DECREASING' ? 'text-red-400' :
                        'text-slate-400'
                    }`}>
                        {timeline.conviction_trend === 'INCREASING' && <TrendingUp className="w-4 h-4" />}
                        {timeline.conviction_trend === 'DECREASING' && <Activity className="w-4 h-4" />}
                        {timeline.conviction_trend === 'STABLE' && <Target className="w-4 h-4" />}
                        {timeline.conviction_trend}
                    </span>
                </div>

                {/* Sample Count */}
                <div className="text-xs text-slate-500 text-center">
                    Based on {timeline.sample_count} analysis{timeline.sample_count !== 1 ? 'es' : ''}
                </div>
            </CardContent>
        </Card>
    );
}
