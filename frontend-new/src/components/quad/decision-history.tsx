"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { History, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
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
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <History className="text-purple-400 w-5 h-5 animate-pulse" />
                        Decision History
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-32">
                        <div className="text-slate-400">Loading history...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !history || history.entries.length === 0) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <History className="text-purple-400 w-5 h-5" />
                        Decision History
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-slate-500">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">
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
        <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <History className="text-purple-400 w-5 h-5" />
                        Decision History
                    </div>
                    <span className="text-sm font-normal text-slate-500">
                        {history.total_decisions} decision{history.total_decisions !== 1 ? 's' : ''}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    {history.entries.map((entry) => (
                        <div
                            key={entry.decision_id}
                            className="border border-slate-800 rounded-lg overflow-hidden hover:border-slate-700 transition-colors"
                        >
                            {/* Main Row */}
                            <div
                                className="p-3 cursor-pointer"
                                onClick={() => toggleExpand(entry.decision_id)}
                            >
                                <div className="flex items-center justify-between gap-4">
                                    {/* Timestamp */}
                                    <div className="flex-shrink-0">
                                        <div className="text-xs text-slate-500">
                                            {format(new Date(entry.analysis_timestamp), 'MMM dd')}
                                        </div>
                                        <div className="text-xs text-slate-400 font-mono">
                                            {format(new Date(entry.analysis_timestamp), 'HH:mm')}
                                        </div>
                                    </div>

                                    {/* Bias */}
                                    <div className="flex-shrink-0">
                                        <div className={`text-sm font-medium ${getBiasColorClass(entry.directional_bias)}`}>
                                            {entry.directional_bias}
                                        </div>
                                    </div>

                                    {/* Conviction */}
                                    <div className="flex-shrink-0">
                                        <div className="text-sm font-mono text-slate-200">
                                            {entry.conviction_score.toFixed(1)}%
                                        </div>
                                    </div>

                                    {/* Calibration */}
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs text-slate-500 truncate">
                                            {entry.calibration_version 
                                                ? formatCalibrationVersion(entry.calibration_version)
                                                : 'N/A'}
                                        </div>
                                    </div>

                                    {/* Expand Icon */}
                                    <div className="flex-shrink-0">
                                        {expandedId === entry.decision_id ? (
                                            <ChevronUp className="w-4 h-4 text-slate-500" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-slate-500" />
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {expandedId === entry.decision_id && (
                                <div className="px-3 pb-3 pt-0 border-t border-slate-800 bg-slate-950/50">
                                    <div className="space-y-3 mt-3">
                                        {/* Decision ID */}
                                        <div>
                                            <div className="text-xs text-slate-500 mb-1">Decision ID</div>
                                            <div className="text-xs font-mono text-slate-400 break-all">
                                                {entry.decision_id}
                                            </div>
                                        </div>

                                        {/* Quality Metrics */}
                                        <div className="grid grid-cols-3 gap-3">
                                            <div>
                                                <div className="text-xs text-slate-500">Active</div>
                                                <div className="text-sm text-green-400 font-mono">
                                                    {entry.pillar_count_active}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-slate-500">Placeholder</div>
                                                <div className="text-sm text-yellow-400 font-mono">
                                                    {entry.pillar_count_placeholder}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-xs text-slate-500">Failed</div>
                                                <div className="text-sm text-red-400 font-mono">
                                                    {entry.pillar_count_failed}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Pillar Scores */}
                                        {entry.pillar_scores && Object.keys(entry.pillar_scores).length > 0 && (
                                            <div>
                                                <div className="text-xs text-slate-500 mb-2">Pillar Scores</div>
                                                <div className="grid grid-cols-2 gap-2">
                                                    {Object.entries(entry.pillar_scores).map(([pillar, score]) => (
                                                        <div key={pillar} className="flex justify-between text-xs">
                                                            <span className="text-slate-400 capitalize">{pillar}</span>
                                                            <span className={`font-mono ${
                                                                entry.pillar_biases?.[pillar] 
                                                                    ? getBiasColorClass(entry.pillar_biases[pillar])
                                                                    : 'text-slate-300'
                                                            }`}>
                                                                {score.toFixed(1)}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Versions */}
                                        <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800">
                                            <span className="text-slate-500">
                                                Engine: <span className="text-slate-400 font-mono">{entry.engine_version}</span>
                                            </span>
                                            <span className="text-slate-500">
                                                Contract: <span className="text-slate-400 font-mono">{entry.contract_version}</span>
                                            </span>
                                        </div>

                                        {/* Superseded Badge */}
                                        {entry.is_superseded && (
                                            <div className="text-xs text-yellow-600 bg-yellow-950/20 px-2 py-1 rounded border border-yellow-900/30">
                                                ⚠️ Superseded by newer analysis
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
