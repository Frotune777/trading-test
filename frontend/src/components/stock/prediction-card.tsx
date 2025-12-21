"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { TrendingUp, TrendingDown, Target, Zap, Brain, BarChart3 } from 'lucide-react';

interface Props {
    symbol: string;
}

export default function PredictionCard({ symbol }: Props) {
    // Mock prediction reasoning - in production, this would come from your ML model
    const reasons = [
        { factor: 'Strong RSI momentum', impact: 'Bullish', weight: 35 },
        { factor: 'Golden Cross (MA50/MA200)', impact: 'Bullish', weight: 30 },
        { factor: 'Volume increase +45%', impact: 'Bullish', weight: 20 },
        { factor: 'Positive earnings surprise', impact: 'Bullish', weight: 15 },
    ];

    return (
        <Card className="bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Zap className="text-yellow-400 w-5 h-5" />
                    AI Prediction
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Direction (5D)</span>
                    <span className="flex items-center gap-1 text-green-400 font-bold">
                        <TrendingUp className="w-4 h-4" /> UP
                    </span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Confidence</span>
                    <span className="text-slate-200">84.2%</span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-slate-400">Target Price</span>
                    <span className="text-slate-200 font-mono">₹2,845.00</span>
                </div>

                {/* Risk Score */}
                <div className="pt-2 border-t border-slate-800">
                    <div className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Risk Score</div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                        <div className="bg-orange-500 h-2 rounded-full w-[35%]"></div>
                    </div>
                </div>

                {/* NEW: Prediction Reasoning */}
                <div className="pt-3 border-t border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                        <Brain className="w-4 h-4 text-purple-400" />
                        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                            Why This Prediction?
                        </span>
                    </div>
                    <div className="space-y-2">
                        {reasons.map((reason, idx) => (
                            <div key={idx} className="flex items-start justify-between gap-2 text-xs">
                                <div className="flex items-start gap-2 flex-1">
                                    <BarChart3 className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" />
                                    <span className="text-slate-300">{reason.factor}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-green-400 font-medium">{reason.weight}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
