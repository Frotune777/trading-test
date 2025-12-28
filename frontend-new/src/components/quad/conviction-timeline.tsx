"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { TrendingUp, Activity, Target, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
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
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="text-primary w-5 h-5 animate-pulse" />
                        Conviction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-muted-foreground">Loading timeline...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !timeline) {
        return (
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="text-primary w-5 h-5" />
                        Conviction Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-destructive">
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
        bias: (point as any).directional_bias || (point as any).bias,
        label: format(new Date(point.timestamp), 'MMM dd HH:mm'),
    }));

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-card border border-border p-3 rounded shadow-lg">
                    <div className="text-xs text-muted-foreground mb-1">{data.label}</div>
                    <div className="text-sm font-mono text-foreground font-black">
                        Conviction: {data.conviction.toFixed(1)}%
                    </div>
                    <div className={cn("text-sm font-bold", getBiasColorClass(data.bias))}>
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
            case 'BULLISH': return 'hsl(var(--success))';
            case 'BEARISH': return 'hsl(var(--destructive))';
            default: return 'hsl(var(--muted-foreground))';
        }
    };

    return (
        <Card className="bg-card border-border shadow-xl">
            <CardHeader className="py-2 border-b border-border/50">
                <CardTitle className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] font-black text-muted-foreground">
                    <Activity className="text-primary w-3.5 h-3.5" />
                    Conviction Timeline
                </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 p-4 space-y-4">
                {/* Chart */}
                <div className="h-48 min-w-0">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                            <XAxis 
                                dataKey="label" 
                                stroke="var(--muted-foreground)"
                                tick={{ fill: 'var(--muted-foreground)', fontSize: 8 }}
                                angle={-45}
                                textAnchor="end"
                                height={40}
                            />
                            <YAxis 
                                domain={[0, 100]}
                                stroke="var(--muted-foreground)"
                                tick={{ fill: 'var(--muted-foreground)', fontSize: 8 }}
                                width={30}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine y={50} stroke="var(--border)" strokeDasharray="3 3" />
                            <Line 
                                type="monotone" 
                                dataKey="conviction" 
                                stroke={getLineColor() || 'var(--primary)'}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 0 }}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-4 gap-2 pt-4 border-t border-border">
                    {/* Average Conviction */}
                    <div>
                        <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Avg</div>
                        <div className="text-base font-black text-foreground tabular-nums">
                            {timeline.average_conviction.toFixed(0)}%
                        </div>
                    </div>

                    {/* Volatility */}
                    <div>
                        <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Vol</div>
                        <div className={cn("text-base font-black tabular-nums",
                            timeline.conviction_volatility < 10 ? 'text-success' :
                            timeline.conviction_volatility < 20 ? 'text-warning' :
                            'text-destructive'
                        )}>
                            {timeline.conviction_volatility.toFixed(1)}
                        </div>
                    </div>

                    {/* Bias Consistency */}
                    <div>
                        <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Cons</div>
                        <div className={cn("text-base font-black tabular-nums",
                            timeline.bias_consistency >= 80 ? 'text-success' :
                            timeline.bias_consistency >= 60 ? 'text-warning' :
                            'text-destructive'
                        )}>
                            {timeline.bias_consistency.toFixed(0)}%
                        </div>
                    </div>

                    {/* Recent Bias Streak */}
                    <div>
                        <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Streak</div>
                        <div className={cn("text-base font-black italic", getBiasColorClass(timeline.recent_bias))}>
                            {timeline.bias_streak_count}x
                        </div>
                    </div>
                </div>

                {/* Trend Indicator */}
                <div className="flex items-center justify-between pt-2 border-t border-border">
                    <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Trend</span>
                    <span className={cn("flex items-center gap-1 text-[9px] font-black px-2 py-0.5 rounded-full border",
                        timeline.conviction_trend === 'INCREASING' ? 'text-success bg-success/10 border-success/20' :
                        timeline.conviction_trend === 'DECREASING' ? 'text-destructive bg-destructive/10 border-destructive/20' :
                        'text-muted-foreground bg-muted border-border'
                    )}>
                        {timeline.conviction_trend === 'INCREASING' && <TrendingUp className="w-2.5 h-2.5" />}
                        {timeline.conviction_trend}
                    </span>
                </div>

                {/* Sample Count */}
                <div className="text-[7px] text-muted-foreground/40 text-center uppercase tracking-[0.2em]">
                    SAMPLED FROM {timeline.sample_count} ENGINE STATES
                </div>
            </CardContent>
        </Card>
    );
}
