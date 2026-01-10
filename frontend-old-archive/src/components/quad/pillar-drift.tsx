"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { BarChart3, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
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
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="text-orange-400 w-5 h-5 animate-pulse" />
                        Pillar Drift
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-slate-400">Loading drift data...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !drift) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="text-orange-400 w-5 h-5" />
                        Pillar Drift
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-400">
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
        <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="text-orange-400 w-5 h-5" />
                    Pillar Drift (Latest vs Previous)
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Drift Classification */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <span className="text-sm text-slate-400">Classification</span>
                    <span className={`text-sm font-bold ${getDriftColorClass(drift.drift_classification)}`}>
                        {drift.drift_classification}
                    </span>
                </div>

                {/* Pillar Drift Bars */}
                <div className="space-y-3">
                    {pillars.map(pillar => {
                        const delta = drift.score_deltas[pillar];
                        const biasChange = drift.bias_changes[pillar];
                        const isPlaceholder = drift.current_snapshot.placeholder_pillars.includes(pillar);
                        
                        // Calculate bar width percentage (0-100%)
                        const barWidth = (Math.abs(delta) / maxAbsDelta) * 100;
                        const isPositive = delta > 0;
                        const isNeutral = Math.abs(delta) < 0.1;

                        return (
                            <div key={pillar} className="space-y-1">
                                {/* Pillar Name and Delta */}
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-slate-300 capitalize flex items-center gap-2">
                                        {pillar}
                                        {isPlaceholder && (
                                            <span className="text-xs text-yellow-600 bg-yellow-950/30 px-1.5 py-0.5 rounded">
                                                placeholder
                                            </span>
                                        )}
                                    </span>
                                    <div className="flex items-center gap-2">
                                        <span className={`font-mono text-sm ${
                                            isNeutral ? 'text-slate-500' :
                                            isPositive ? 'text-green-400' : 'text-red-400'
                                        }`}>
                                            {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                                        </span>
                                        {biasChange && (
                                            <span className="text-xs text-slate-500">
                                                {biasChange.from.slice(0, 1)}→{biasChange.to.slice(0, 1)}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Drift Bar */}
                                <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
                                    {!isNeutral && (
                                        <div
                                            className={`absolute top-0 h-full rounded-full transition-all ${
                                                isPositive ? 'bg-green-500/70' : 'bg-red-500/70'
                                            }`}
                                            style={{
                                                width: `${barWidth}%`,
                                                left: isPositive ? '50%' : `${50 - barWidth}%`,
                                            }}
                                        />
                                    )}
                                    {/* Center line */}
                                    <div className="absolute left-1/2 top-0 w-px h-full bg-slate-600" />
                                </div>

                                {/* Bias Change Detail */}
                                {biasChange && (
                                    <div className="flex items-center gap-2 text-xs">
                                        <span className={getBiasColorClass(biasChange.from)}>
                                            {biasChange.from}
                                        </span>
                                        <span className="text-slate-600">→</span>
                                        <span className={getBiasColorClass(biasChange.to)}>
                                            {biasChange.to}
                                        </span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Top Movers */}
                {drift.top_movers && drift.top_movers.length > 0 && (
                    <div className="pt-3 border-t border-slate-800">
                        <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">
                            Top Movers
                        </div>
                        <div className="space-y-2">
                            {drift.top_movers.slice(0, 3).map((mover, idx) => (
                                <div key={idx} className="flex items-center justify-between text-xs">
                                    <span className="text-slate-300 capitalize">{mover.pillar}</span>
                                    <div className="flex items-center gap-2">
                                        {mover.delta > 0 ? (
                                            <TrendingUp className="w-3 h-3 text-green-400" />
                                        ) : mover.delta < 0 ? (
                                            <TrendingDown className="w-3 h-3 text-red-400" />
                                        ) : (
                                            <Minus className="w-3 h-3 text-slate-500" />
                                        )}
                                        <span className={`font-mono ${
                                            mover.delta > 0 ? 'text-green-400' :
                                            mover.delta < 0 ? 'text-red-400' :
                                            'text-slate-500'
                                        }`}>
                                            {mover.delta > 0 ? '+' : ''}{mover.delta.toFixed(1)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Drift Summary */}
                <div className="pt-3 border-t border-slate-800">
                    <div className="text-xs text-slate-400 leading-relaxed">
                        {drift.drift_summary}
                    </div>
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-800 text-xs">
                    <div>
                        <div className="text-slate-500">Total Drift</div>
                        <div className="text-slate-200 font-mono">{drift.total_drift_score.toFixed(1)} pts</div>
                    </div>
                    <div>
                        <div className="text-slate-500">Max Change</div>
                        <div className="text-slate-200 font-mono capitalize">
                            {drift.max_drift_pillar} ({drift.max_drift_magnitude.toFixed(1)})
                        </div>
                    </div>
                </div>

                {/* Calibration Change Warning */}
                {drift.calibration_changed && (
                    <div className="text-xs text-orange-400 bg-orange-950/20 p-2 rounded border border-orange-900/30">
                        ⚠️ Calibration version changed between analyses
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
