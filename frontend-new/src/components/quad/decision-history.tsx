"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { History, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { QuadService, getBiasColorClass, formatCalibrationVersion } from '@/lib/api/quad';
import type { DecisionHistory as DecisionHistoryType, DecisionHistoryEntry } from '@/lib/api/types';
import { format } from 'date-fns';

interface Props {
    symbol: string;
    limit?: number;
}

export default function DecisionHistory({ symbol, limit = 10 }: Props) {
    const [history, setHistory] = useState<DecisionHistoryType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await QuadService.getDecisionHistory(symbol, limit);
                setHistory(data);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Failed to fetch decision history');
                console.error('Error fetching decision history:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [symbol, limit]);

    if (loading) {
        return (
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xs uppercase tracking-widest font-black text-muted-foreground">
                        <History className="text-primary w-4 h-4 animate-pulse" />
                        Decision History
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-32">
                        <div className="text-muted-foreground text-xs font-bold animate-pulse">RECOLLECTING TIMELINER...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !history || history.entries.length === 0) {
        return (
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xs uppercase tracking-widest font-black text-muted-foreground">
                        <History className="text-primary w-4 h-4" />
                        Decision History
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-muted-foreground/60 p-8 border border-dashed border-border rounded-xl justify-center">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm font-bold">
                            {error || 'No decision history available'}
                        </span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const toggleExpand = (id: string) => {
        setExpandedId(expandedId === id ? null : id);
    };

    return (
        <Card className="bg-card border-border shadow-2xl">
            <CardHeader className="border-b border-border/50 bg-secondary/30">
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs uppercase tracking-widest font-black text-foreground">
                        <History className="text-primary w-4 h-4" />
                        Historical Decision Audit
                    </div>
                    <Badge variant="secondary" className="font-black text-[10px] tracking-tighter">
                        {history.total_decisions} SAMPLES
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <div className="divide-y divide-border">
                    {history.entries.map((entry) => (
                        <div
                            key={entry.decision_id}
                            className="overflow-hidden hover:bg-muted/30 transition-colors"
                        >
                            {/* Main Row */}
                            <div
                                className="p-4 cursor-pointer"
                                onClick={() => toggleExpand(entry.decision_id)}
                            >
                                <div className="flex items-center justify-between gap-6">
                                    {/* Timestamp */}
                                    <div className="flex-shrink-0">
                                        <div className="text-[10px] uppercase font-black text-muted-foreground mb-0.5">
                                            {format(new Date(entry.analysis_timestamp), 'MMM dd')}
                                        </div>
                                        <div className="text-xs font-black text-foreground tabular-nums opacity-60">
                                            {format(new Date(entry.analysis_timestamp), 'HH:mm')}
                                        </div>
                                    </div>

                                    {/* Bias */}
                                    <div className="flex-shrink-0 min-w-[80px]">
                                        <Badge variant="outline" className={cn("font-black text-[10px] tracking-widest", getBiasColorClass(entry.directional_bias))}>
                                            {entry.directional_bias}
                                        </Badge>
                                    </div>

                                    {/* Conviction */}
                                    <div className="flex-shrink-0">
                                        <div className="text-sm font-black text-foreground tabular-nums">
                                            {entry.conviction_score.toFixed(1)}%
                                        </div>
                                    </div>

                                    {/* Calibration */}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-[10px] text-muted-foreground font-bold truncate opacity-40">
                                            {entry.calibration_version 
                                                ? formatCalibrationVersion(entry.calibration_version)
                                                : 'N/A'}
                                        </div>
                                    </div>

                                    {/* Expand Icon */}
                                    <div className="flex-shrink-0">
                                        {expandedId === entry.decision_id ? (
                                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {expandedId === entry.decision_id && (
                                <div className="px-6 pb-6 pt-2 bg-muted/20 border-t border-border">
                                    <div className="space-y-4 mt-4">
                                        {/* Decision ID */}
                                        <div className="bg-background/50 p-3 rounded-lg border border-border">
                                            <div className="text-[9px] uppercase font-black text-muted-foreground mb-1 tracking-widest">Internal Decision Token</div>
                                            <div className="text-[10px] font-black text-primary break-all uppercase tracking-tighter">
                                                {entry.decision_id}
                                            </div>
                                        </div>

                                        {/* Quality Metrics */}
                                        <div className="grid grid-cols-3 gap-4">
                                            <div className="bg-success/5 p-3 rounded-xl border border-success/20">
                                                <div className="text-[9px] uppercase font-black text-success mb-1 tracking-widest opacity-60">Active</div>
                                                <div className="text-lg font-black text-success tabular-nums">
                                                    {entry.pillar_count_active}
                                                </div>
                                            </div>
                                            <div className="bg-warning/5 p-3 rounded-xl border border-warning/20">
                                                <div className="text-[9px] uppercase font-black text-warning mb-1 tracking-widest opacity-60">Mocked</div>
                                                <div className="text-lg font-black text-warning tabular-nums">
                                                    {entry.pillar_count_placeholder}
                                                </div>
                                            </div>
                                            <div className="bg-destructive/5 p-3 rounded-xl border border-destructive/20">
                                                <div className="text-[9px] uppercase font-black text-destructive mb-1 tracking-widest opacity-60">Failed</div>
                                                <div className="text-lg font-black text-destructive tabular-nums">
                                                    {entry.pillar_count_failed}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Pillar Scores */}
                                        {entry.pillar_scores && Object.keys(entry.pillar_scores).length > 0 && (
                                            <div className="bg-muted/30 p-4 rounded-xl border border-border">
                                                <div className="text-[9px] uppercase font-black text-muted-foreground mb-4 tracking-widest">Pillar Contribution Breakdown</div>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
                                                    {Object.entries(entry.pillar_scores).map(([pillar, score]) => (
                                                        <div key={pillar} className="flex justify-between text-[11px] items-center group">
                                                            <span className="text-muted-foreground font-bold capitalize group-hover:text-foreground transition-colors">{pillar}</span>
                                                            <span className={cn("font-black tabular-nums",
                                                                entry.pillar_biases?.[pillar] 
                                                                    ? getBiasColorClass(entry.pillar_biases[pillar])
                                                                    : 'text-muted-foreground'
                                                            )}>
                                                                {score.toFixed(1)}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Versions */}
                                        <div className="flex items-center justify-between text-[9px] pt-4 border-t border-border uppercase font-black tracking-[0.2em] opacity-40">
                                            <span>
                                                Core: <span className="text-foreground">{entry.engine_version}</span>
                                            </span>
                                            <span>
                                                Interface: <span className="text-foreground">{entry.contract_version}</span>
                                            </span>
                                        </div>

                                        {/* Superseded Badge */}
                                        {entry.is_superseded && (
                                            <div className="text-[10px] font-black text-warning bg-warning/5 px-3 py-2 rounded-lg border border-warning/20 flex items-center gap-2">
                                                <AlertCircle className="w-3.5 h-3.5" />
                                                ANALYSIS SUPERSEDED BY RECENT CALIBRATION
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
