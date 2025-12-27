"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { BarChart3, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { QuadService, getBiasColorClass, getDriftColorClass } from '@/lib/api/quad';
import type { PillarDriftMeasurement as PillarDriftType } from '@/lib/api/types';

interface Props {
    symbol: string;
}

export default function PillarDrift({ symbol }: Props) {
    const [drift, setDrift] = useState<PillarDriftType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDrift = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await QuadService.getPillarDrift(symbol);
                setDrift(data);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Failed to fetch pillar drift');
                console.error('Error fetching pillar drift:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchDrift();
    }, [symbol]);

    if (loading) {
        return (
            <Card className="bg-card border-border shadow-xl">
                <CardHeader className="border-b border-border/50">
                    <CardTitle className="flex items-center gap-2 text-xs uppercase tracking-[0.2rem] font-black text-muted-foreground">
                        <BarChart3 className="text-warning w-4 h-4 animate-pulse" />
                        Pillar Drift
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-muted-foreground font-mono text-xs tracking-widest">ANALYZING DRIFT MATRIX...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !drift) {
        return (
            <Card className="bg-card border-border">
                <CardHeader className="border-b border-border/50">
                    <CardTitle className="flex items-center gap-2 text-xs uppercase tracking-[0.2rem] font-black text-muted-foreground">
                        <BarChart3 className="text-warning w-4 h-4" />
                        Pillar Drift
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{error || 'No drift data available'}</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Get pillar names sorted by absolute drift magnitude
    const pillars = Object.keys(drift.score_deltas).sort((a, b) => 
        Math.abs(drift.score_deltas[b]) - Math.abs(drift.score_deltas[a])
    );

    // Calculate max absolute delta for scaling bars
    const maxAbsDelta = Math.max(...Object.values(drift.score_deltas).map(Math.abs), 1);

    return (
        <Card className="bg-card border-border shadow-2xl overflow-hidden">
            <CardHeader className="border-b border-border/50 bg-secondary/30">
                <CardTitle className="flex items-center gap-2 text-xs uppercase tracking-[0.25rem] font-black text-foreground">
                    <BarChart3 className="text-primary w-4 h-4" />
                    Structural Drift Analytics
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                {/* Drift Classification Header */}
                <div className="px-6 py-4 bg-muted/30 flex items-center justify-between border-b border-border">
                    <span className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Engine Classification</span>
                    <Badge variant="outline" className={cn("font-black tracking-tighter", getDriftColorClass(drift.drift_classification))}>
                        {drift.drift_classification}
                    </Badge>
                </div>

                <div className="p-6 space-y-6">
                    {/* Pillar Drift Bars */}
                    <div className="space-y-6">
                        {pillars.map(pillar => {
                            const delta = drift.score_deltas[pillar];
                            const biasChange = drift.bias_changes[pillar];
                            const isPlaceholder = drift.current_snapshot.placeholder_pillars.includes(pillar);
                            
                            // Calculate bar width percentage (0-100%)
                            const barWidth = (Math.abs(delta) / maxAbsDelta) * 100;
                            const isPositive = delta > 0;
                            const isNeutral = Math.abs(delta) < 0.1;

                            return (
                                <div key={pillar} className="space-y-2">
                                    {/* Pillar Name and Delta */}
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-foreground font-bold capitalize flex items-center gap-2">
                                            {pillar}
                                            {isPlaceholder && (
                                                <span className="text-[9px] font-black text-warning bg-warning/10 border border-warning/20 px-1.5 py-0.5 rounded uppercase">
                                                    placeholder
                                                </span>
                                            )}
                                        </span>
                                        <div className="flex items-center gap-3">
                                            <span className={cn("font-black text-sm tabular-nums",
                                                isNeutral ? 'text-muted-foreground' :
                                                isPositive ? 'text-success' : 'text-destructive'
                                            )}>
                                                {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                                            </span>
                                            {biasChange && (
                                                <Badge variant="secondary" className="text-[9px] font-black opacity-60">
                                                    {biasChange.from.slice(0, 1)} → {biasChange.to.slice(0, 1)}
                                                </Badge>
                                            )}
                                        </div>
                                    </div>

                                    {/* Drift Bar Container */}
                                    <div className="relative h-3 bg-muted/50 rounded-full overflow-hidden border border-border/50">
                                        {!isNeutral && (
                                            <div
                                                className={cn("absolute top-0 h-full rounded-full transition-all duration-700",
                                                    isPositive ? 'bg-success' : 'bg-destructive'
                                                )}
                                                style={{
                                                    width: `${barWidth}%`,
                                                    left: isPositive ? '50%' : `${50 - barWidth}%`,
                                                }}
                                            />
                                        )}
                                        {/* Center line */}
                                        <div className="absolute left-1/2 top-0 w-0.5 h-full bg-foreground/20 z-10" />
                                    </div>

                                    {/* Bias Change Detail */}
                                    {biasChange && (
                                        <div className="flex items-center gap-2 text-[10px] bg-secondary/20 p-2 rounded-lg border border-border/30">
                                            <span className={cn("font-black", getBiasColorClass(biasChange.from))}>
                                                {biasChange.from}
                                            </span>
                                            <span className="text-muted-foreground opacity-40">→</span>
                                            <span className={cn("font-black", getBiasColorClass(biasChange.to))}>
                                                {biasChange.to}
                                            </span>
                                            <div className="ml-auto text-muted-foreground italic opacity-60">Bias Transition detected</div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Footer Info Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-border">
                        <div className="bg-muted/30 p-4 rounded-xl border border-border">
                            <div className="text-[10px] uppercase font-black text-muted-foreground mb-1 tracking-widest">Aggregate Displacement</div>
                            <div className="text-xl font-black text-foreground tabular-nums">{drift.total_drift_score.toFixed(1)} <span className="text-xs text-muted-foreground font-normal">pts</span></div>
                        </div>
                        <div className="bg-muted/30 p-4 rounded-xl border border-border">
                            <div className="text-[10px] uppercase font-black text-muted-foreground mb-1 tracking-widest">Max Variance Pivot</div>
                            <div className="text-xl font-black text-foreground capitalize tracking-tight group">
                                {drift.max_drift_pillar} 
                                <span className="text-xs text-muted-foreground ml-2 opacity-60 group-hover:opacity-100 transition-opacity">
                                    ({drift.max_drift_magnitude.toFixed(1)})
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Summary Narrative */}
                    <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl relative overflow-hidden group">
                        <div className="absolute top-0 bottom-0 left-0 w-1 bg-primary" />
                        <div className="text-xs text-foreground/80 leading-relaxed italic relative z-10">
                            "{drift.drift_summary}"
                        </div>
                    </div>

                    {/* Calibration Warning */}
                    {drift.calibration_changed && (
                        <div className="text-[10px] font-black text-warning bg-warning/5 p-3 rounded-lg border border-warning/20 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            ENGINE CALIBRATION SHIFT DETECTED - INTERPRET DRIFT WITH CAUTION
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
