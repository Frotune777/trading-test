'use client';

import { useState } from 'react';
import { type Decision } from '@/lib/api/decisions';
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

interface DecisionCardProps {
    decision: Decision;
}

export default function DecisionCard({ decision }: DecisionCardProps) {
    const [expanded, setExpanded] = useState(false);

    const getDecisionColor = (action: string) => {
        switch (action) {
            case 'BUY': return 'text-green-600 bg-green-100 dark:bg-green-900/30';
            case 'SELL': return 'text-red-600 bg-red-100 dark:bg-red-900/30';
            default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800';
        }
    };

    const getDecisionIcon = (action: string) => {
        switch (action) {
            case 'BUY': return <TrendingUp className="w-5 h-5" />;
            case 'SELL': return <TrendingDown className="w-5 h-5" />;
            default: return <Minus className="w-5 h-5" />;
        }
    };

    const getConvictionColor = (conviction: number) => {
        if (conviction >= 80) return 'text-green-600';
        if (conviction >= 60) return 'text-blue-600';
        if (conviction >= 40) return 'text-yellow-600';
        return 'text-gray-600';
    };

    const getRiskColor = (status: string) => {
        switch (status) {
            case 'PASS': return 'text-green-600';
            case 'WARN': return 'text-yellow-600';
            case 'FAIL': return 'text-red-600';
            default: return 'text-gray-600';
        }
    };

    // Get top 3 causes from causal graph
    const topCauses = decision.causal_graph
        .sort((a, b) => (b.confidence * (b.magnitude || 1)) - (a.confidence * (a.magnitude || 1)))
        .slice(0, 3);

    const hasRiskWarnings = Object.values(decision.risk_checks).some(v => v === 'WARN' || v === 'FAIL');

    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full font-semibold ${getDecisionColor(decision.final_decision)}`}>
                            {getDecisionIcon(decision.final_decision)}
                            <span>{decision.final_decision}</span>
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                {decision.symbol}
                            </h3>
                            <p className="text-xs text-gray-500">
                                {new Date(decision.timestamp).toLocaleString()}
                            </p>
                        </div>
                    </div>

                    {/* Conviction Gauge */}
                    <div className="text-right">
                        <p className="text-xs text-gray-600 dark:text-gray-400">Conviction</p>
                        <p className={`text-3xl font-bold ${getConvictionColor(decision.conviction)}`}>
                            {decision.conviction}
                        </p>
                        <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full mt-1">
                            <div
                                className={`h-full rounded-full ${getConvictionColor(decision.conviction).replace('text-', 'bg-')}`}
                                style={{ width: `${decision.conviction}%` }}
                            />
                        </div>
                    </div>
                </div>

                {/* Mode Badge */}
                <div className="mt-2 flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${decision.mode === 'LIVE'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        }`}>
                        {decision.mode}
                    </span>
                    {decision.inputs.ml?.shadow_mode && (
                        <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                            ML Shadow Mode
                        </span>
                    )}
                    {decision.executed && (
                        <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                            Executed
                        </span>
                    )}
                </div>
            </div>

            {/* Summary */}
            <div className="p-4 space-y-3">
                {/* Top Causes */}
                <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Top Contributing Factors
                    </h4>
                    <div className="space-y-2">
                        {topCauses.map((cause, i) => (
                            <div key={i} className="flex items-start gap-2">
                                <div className="flex-shrink-0 w-12 text-right">
                                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                        {(cause.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="flex-1">
                                    <p className="text-sm text-gray-900 dark:text-white font-medium">
                                        {cause.cause}
                                    </p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">
                                        → {cause.effect}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Warnings */}
                {hasRiskWarnings && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                        <div className="flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                            <div className="flex-1">
                                <h5 className="text-sm font-semibold text-yellow-900 dark:text-yellow-100">
                                    Risk Warnings
                                </h5>
                                <div className="mt-1 space-y-1">
                                    {Object.entries(decision.risk_checks).map(([key, value]) => (
                                        value !== 'PASS' && (
                                            <div key={key} className="flex items-center gap-2 text-xs">
                                                <span className={`font-medium ${getRiskColor(value)}`}>
                                                    {value}
                                                </span>
                                                <span className="text-yellow-700 dark:text-yellow-300">
                                                    {key.replace(/_/g, ' ')}
                                                </span>
                                            </div>
                                        )
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Expand Button */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="w-full flex items-center justify-center gap-2 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                >
                    {expanded ? (
                        <>
                            <ChevronUp className="w-4 h-4" />
                            Hide Details
                        </>
                    ) : (
                        <>
                            <ChevronDown className="w-4 h-4" />
                            Show Full Decision Ledger
                        </>
                    )}
                </button>
            </div>

            {/* Expanded Details */}
            {expanded && (
                <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4 bg-gray-50 dark:bg-gray-900/50">
                    {/* Inputs */}
                    <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            Inputs
                        </h4>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                                <span className="text-gray-600 dark:text-gray-400">Price:</span>
                                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                                    ₹{decision.inputs.price.toFixed(2)}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-600 dark:text-gray-400">Regime:</span>
                                <span className="ml-2 font-medium text-gray-900 dark:text-white">
                                    {decision.inputs.regime}
                                </span>
                            </div>
                            {decision.inputs.ml && (
                                <>
                                    <div>
                                        <span className="text-gray-600 dark:text-gray-400">ML Prediction:</span>
                                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                                            {decision.inputs.ml.prediction}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="text-gray-600 dark:text-gray-400">ML Confidence:</span>
                                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                                            {(decision.inputs.ml.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Indicators */}
                        <div className="mt-2">
                            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Indicators:</p>
                            <div className="grid grid-cols-3 gap-2 text-xs">
                                {Object.entries(decision.inputs.indicators).map(([key, value]) => (
                                    <div key={key} className="flex justify-between">
                                        <span className="text-gray-600 dark:text-gray-400">{key}:</span>
                                        <span className="font-medium text-gray-900 dark:text-white">
                                            {typeof value === 'number' ? value.toFixed(2) : value}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Pillar Weights */}
                    <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            Pillar Weights (Q/U/A/D)
                        </h4>
                        <div className="flex gap-2">
                            {Object.entries(decision.weights).map(([pillar, weight]) => (
                                <div key={pillar} className="flex-1 text-center">
                                    <p className="text-xs text-gray-600 dark:text-gray-400">{pillar}</p>
                                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                                        {(weight * 100).toFixed(0)}%
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* All Causal Factors */}
                    <div>
                        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            Complete Causal Graph
                        </h4>
                        <div className="space-y-2">
                            {decision.causal_graph.map((cause, i) => (
                                <div key={i} className="bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                                                {cause.cause}
                                            </p>
                                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                                                → {cause.effect}
                                            </p>
                                        </div>
                                        <div className="text-right ml-2">
                                            <p className="text-xs font-semibold text-gray-900 dark:text-white">
                                                {(cause.confidence * 100).toFixed(0)}%
                                            </p>
                                            {cause.magnitude && (
                                                <p className="text-xs text-gray-600 dark:text-gray-400">
                                                    {cause.magnitude > 0 ? '+' : ''}{cause.magnitude.toFixed(1)}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Execution Details */}
                    {decision.executed && (
                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                Execution Details
                            </h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="text-gray-600 dark:text-gray-400">Execution Price:</span>
                                    <span className="ml-2 font-medium text-gray-900 dark:text-white">
                                        ₹{decision.execution_price?.toFixed(2)}
                                    </span>
                                </div>
                                {decision.actual_pnl !== undefined && (
                                    <div>
                                        <span className="text-gray-600 dark:text-gray-400">P&L:</span>
                                        <span className={`ml-2 font-medium ${decision.actual_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {decision.actual_pnl >= 0 ? '+' : ''}₹{decision.actual_pnl.toFixed(2)}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
