
import React, { useEffect, useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface PillarScore {
    score: number;
    bias: string;
    is_placeholder: boolean;
    weight: number;
}

interface AnalysisProps {
    latestAnalysis: {
        symbol: string;
        pillar_scores: Record<string, PillarScore>;
        analysis_timestamp?: string;
    } | null;
}

interface PillarHistory {
    [key: string]: { score: number; timestamp: number }[];
}

const HISTORY_LENGTH = 20;

const PillarLiveTrend: React.FC<AnalysisProps> = ({ latestAnalysis }) => {
    const [history, setHistory] = useState<PillarHistory>({});
    const lastUpdateRef = useRef<string | null>(null);

    useEffect(() => {
        if (!latestAnalysis?.pillar_scores) return;

        // Prevent duplicate updates if analysis object identity hasn't changed meaningfully
        const updateKey = `${latestAnalysis.symbol}-${latestAnalysis.analysis_timestamp || Date.now()}`;
        if (lastUpdateRef.current === updateKey) return;
        lastUpdateRef.current = updateKey;

        setHistory(prev => {
            const next = { ...prev };

            Object.entries(latestAnalysis.pillar_scores).forEach(([name, p]) => {
                if (!next[name]) next[name] = [];

                // Add new point
                next[name] = [
                    ...next[name],
                    { score: p.score, timestamp: Date.now() }
                ].slice(-HISTORY_LENGTH); // Keep last N
            });
            return next;
        });
    }, [latestAnalysis]);

    if (!latestAnalysis) {
        return (
            <Card className="h-[400px]">
                <CardContent className="flex items-center justify-center h-full text-muted-foreground">
                    Waiting for analysis stream...
                </CardContent>
            </Card>
        );
    }

    // Calculate drift statistics
    const getDriftStats = (pillarName: string, currentScore: number) => {
        const data = history[pillarName];
        if (!data || data.length < 5) return { drift: 0, velocity: 'stable' };

        const oldScore = data[data.length - 5].score; // Compare vs 5 ticks ago
        const drift = currentScore - oldScore;

        let velocity = 'stable';
        if (drift > 5) velocity = 'surging';
        if (drift < -5) velocity = 'crashing';

        return { drift, velocity };
    };

    const getPillarColor = (bias: string) => {
        if (bias === 'BULLISH') return '#22c55e'; // Green
        if (bias === 'BEARISH') return '#ef4444'; // Red
        return '#94a3b8'; // Neutral gray
    };

    return (
        <Card className="h-[400px] flex flex-col">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                    <span className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-indigo-500" />
                        Pillar Momentum
                    </span>
                    <Badge variant="outline">Live Drift</Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 overflow-y-auto">
                {Object.entries(latestAnalysis.pillar_scores).map(([name, pillar]) => {
                    const stats = getDriftStats(name, pillar.score);
                    const chartData = history[name] || [];
                    const color = getPillarColor(pillar.bias);

                    return (
                        <div key={name} className="flex flex-col gap-1 p-2 rounded-lg border bg-card/50">
                            <div className="flex justify-between items-center">
                                <span className="text-xs font-medium uppercase text-muted-foreground">
                                    {name}
                                </span>
                                <div className="flex items-center gap-1">
                                    {stats.drift > 2 ? <TrendingUp className="h-3 w-3 text-green-500" /> :
                                        stats.drift < -2 ? <TrendingDown className="h-3 w-3 text-red-500" /> :
                                            <Minus className="h-3 w-3 text-muted-foreground" />}
                                    <span className={`text-xs font-bold ${stats.drift > 0 ? 'text-green-500' : stats.drift < 0 ? 'text-red-500' : ''
                                        }`}>
                                        {pillar.score.toFixed(0)}
                                    </span>
                                </div>
                            </div>

                            <div className="h-12 w-full mt-1">
                                {chartData.length > 1 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={chartData}>
                                            <YAxis domain={[0, 100]} hide />
                                            <Line
                                                type="monotone"
                                                dataKey="score"
                                                stroke={color}
                                                strokeWidth={2}
                                                dot={false}
                                                isAnimationActive={false}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full w-full bg-muted/20 rounded animate-pulse" />
                                )}
                            </div>
                        </div>
                    );
                })}
            </CardContent>
        </Card>
    );
};

export default PillarLiveTrend;
