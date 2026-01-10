'use client';

import { useState } from 'react';
import InsiderSentinel from '@/components/analytics/InsiderSentinel';
import PeerComparison from '@/components/analytics/PeerComparison';
import MLModelMetrics from '@/components/analytics/MLModelMetrics';
import PillarWeightConfig from '@/components/analytics/PillarWeightConfig';
import {
    LineChart, Brain, BarChart3, Settings,
    Search, Shield, TrendingUp, Cpu
} from 'lucide-react';

export default function AnalyticsPage() {
    const [symbol, setSymbol] = useState('RELIANCE');
    const [searchInput, setSearchInput] = useState('RELIANCE');

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchInput.trim()) {
            setSymbol(searchInput.trim().toUpperCase());
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 space-y-8">
            {/* Header & Search */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-gray-900 text-white p-8 rounded-2xl shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                    <Cpu size={140} />
                </div>

                <div className="relative z-10">
                    <h1 className="text-4xl font-black flex items-center gap-3 tracking-tight">
                        <Brain className="w-10 h-10 text-blue-400" />
                        QUAD Intelligence
                    </h1>
                    <p className="text-gray-400 mt-2 text-sm font-medium uppercase tracking-widest">Advanced AI Analytics & Causal Insight Dashboard</p>
                </div>

                <form onSubmit={handleSearch} className="relative z-10 w-full md:w-auto">
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-400 transition-colors" />
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            placeholder="Enter Stock Symbol (e.g. RELIANCE)"
                            className="pl-12 pr-6 py-4 bg-gray-800 border-2 border-gray-700 rounded-xl w-full md:w-80 focus:outline-none focus:border-blue-500 transition-all font-bold text-lg"
                        />
                    </div>
                </form>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Main Column */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Top Row: Sentinel & Peer Comparison */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <InsiderSentinel symbol={symbol} />
                        <PeerComparison symbol={symbol} />
                    </div>

                    {/* Middle Row: ML Performance */}
                    <MLModelMetrics symbol={symbol} />

                    {/* Notice */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800 rounded-xl flex gap-3">
                        <Shield className="w-5 h-5 text-blue-600 shrink-0" />
                        <p className="text-xs text-blue-800 dark:text-blue-300">
                            <strong>Note:</strong> Advanced analytics use a combination of historical backtest data, real-time market sentiment, and insider trading records. ML Accuracy is evaluated on a rolling 30-day window with price target hit criteria within 5 trading sessions.
                        </p>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="lg:col-span-4 space-y-8">
                    <PillarWeightConfig />

                    {/* System Info */}
                    <div className="bg-gray-50 dark:bg-gray-900/30 p-6 rounded-xl border border-gray-100 dark:border-gray-700/50">
                        <h4 className="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-xs mb-4 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-green-600" />
                            Live Model Status
                        </h4>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-gray-500">Model Version</span>
                                <span className="text-xs font-mono font-bold px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">v2.4-stable</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-gray-500">Retraining Cycle</span>
                                <span className="text-xs font-bold text-gray-900 dark:text-white">Daily @ 18:30 IST</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-gray-500">Feature Engineering</span>
                                <span className="text-xs font-bold text-green-600">Active (42 features)</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-gray-500">Prediction Horizon</span>
                                <span className="text-xs font-bold text-gray-900 dark:text-white">T+7 Trading Days</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
