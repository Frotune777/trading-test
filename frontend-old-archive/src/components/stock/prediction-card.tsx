"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { TrendingUp, TrendingDown, Target, Zap, Brain, BarChart3, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { QuadService, formatCalibrationVersion, getBiasColorClass } from '@/lib/api/quad';
import type { TradeIntentResponse, PillarScore } from '@/lib/api/types';

interface Props {
    symbol: string;
}

export default function PredictionCard({ symbol }: Props) {
    const [analysis, setAnalysis] = useState<TradeIntentResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalysis = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await QuadService.getAnalysis(symbol);
                setAnalysis(data);
            } catch (err: any) {
                setError(err.response?.data?.detail || 'Failed to fetch QUAD analysis');
                console.error('Error fetching QUAD analysis:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalysis();
        
        // Refresh every 30 seconds
        const interval = setInterval(fetchAnalysis, 30000);
        return () => clearInterval(interval);
    }, [symbol]);

    if (loading) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Brain className="text-purple-400 w-5 h-5 animate-pulse" />
                        QUAD Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-32">
                        <div className="text-slate-400">Loading analysis...</div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error || !analysis) {
        return (
            <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Brain className="text-purple-400 w-5 h-5" />
                        QUAD Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2 text-red-400">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{error || 'No data available'}</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const biasColorClass = getBiasColorClass(analysis.directional_bias);
    const BiasIcon = analysis.directional_bias === 'BULLISH' ? TrendingUp : 
                     analysis.directional_bias === 'BEARISH' ? TrendingDown : Target;

    // Get pillar scores as array for display
    const pillarScores = Object.entries(analysis.pillar_scores || {})
        .filter(([_, pillar]) => !pillar.is_placeholder)
        .sort((a, b) => b[1].score - a[1].score);

    return (
        <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Brain className="text-purple-400 w-5 h-5" />
                    QUAD Analysis
                    {analysis.contract_version >= "1.1.0" && (
                        <span className="ml-auto text-xs font-normal text-slate-500">
                            v{analysis.contract_version}
                        </span>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Directional Bias */}
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Direction</span>
                    <span className={`flex items-center gap-1 font-bold ${biasColorClass}`}>
                        <BiasIcon className="w-4 h-4" />
                        {analysis.directional_bias}
                    </span>
                </div>

                {/* Conviction Score */}
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Conviction</span>
                    <span className="text-slate-200 font-mono">{analysis.conviction_score.toFixed(1)}%</span>
                </div>

                {/* Execution Readiness */}
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Execution Ready</span>
                    <span className={`flex items-center gap-1 text-sm ${analysis.is_execution_ready ? 'text-green-400' : 'text-red-400'}`}>
                        {analysis.is_execution_ready ? (
                            <><CheckCircle2 className="w-3 h-3" /> Yes</>
                        ) : (
                            <><XCircle className="w-3 h-3" /> No</>
                        )}
                    </span>
                </div>

                {/* Execution Block Reason */}
                {!analysis.is_execution_ready && analysis.execution_block_reason && (
                    <div className="text-xs text-orange-400 bg-orange-950/20 p-2 rounded border border-orange-900/30">
                        ⚠️ {analysis.execution_block_reason.replace(/_/g, ' ')}
                    </div>
                )}

                {/* Quality Metadata */}
                <div className="pt-2 border-t border-slate-800">
                    <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">
                        Analysis Quality
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                            <div className="text-slate-500">Active</div>
                            <div className="text-green-400 font-mono">{analysis.quality.active_pillars}/{analysis.quality.total_pillars}</div>
                        </div>
                        <div>
                            <div className="text-slate-500">Placeholder</div>
                            <div className="text-yellow-400 font-mono">{analysis.quality.placeholder_pillars}</div>
                        </div>
                        <div>
                            <div className="text-slate-500">Failed</div>
                            <div className="text-red-400 font-mono">{analysis.quality.failed_pillars.length}</div>
                        </div>
                    </div>
                </div>

                {/* v1.1: Calibration Version */}
                {analysis.quality.calibration_version && (
                    <div className="text-xs text-slate-500">
                        <span className="text-slate-600">Calibration:</span>{' '}
                        <span className="text-purple-400 font-mono">
                            {formatCalibrationVersion(analysis.quality.calibration_version)}
                        </span>
                    </div>
                )}

                {/* Pillar Breakdown */}
                <div className="pt-3 border-t border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                        <BarChart3 className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                            Pillar Scores
                        </span>
                    </div>
                    <div className="space-y-2">
                        {pillarScores.length > 0 ? (
                            pillarScores.map(([name, pillar]) => (
                                <div key={name} className="flex items-start justify-between gap-2 text-xs">
                                    <div className="flex items-start gap-2 flex-1">
                                        <span className="text-slate-300 capitalize">{name}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`font-medium ${getBiasColorClass(pillar.bias)}`}>
                                            {pillar.score.toFixed(1)}
                                        </span>
                                        <span className={`text-xs ${getBiasColorClass(pillar.bias)}`}>
                                            {pillar.bias}
                                        </span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-slate-500 text-xs">No active pillars</div>
                        )}
                    </div>
                </div>

                {/* Warnings */}
                {analysis.warnings && analysis.warnings.length > 0 && (
                    <div className="pt-2 border-t border-slate-800">
                        <div className="text-xs text-yellow-400 space-y-1">
                            {analysis.warnings.map((warning, idx) => (
                                <div key={idx} className="flex items-start gap-1">
                                    <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                                    <span>{warning}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Reasoning Narrative */}
                {analysis.reasoning && (
                    <div className="pt-2 border-t border-slate-800">
                        <div className="text-xs text-slate-400 leading-relaxed">
                            {analysis.reasoning}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
