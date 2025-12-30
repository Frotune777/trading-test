'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { decisionApi } from '@/lib/api/decisions';
import DecisionCard from '@/components/decisions/DecisionCard';
import DecisionTimeline from '@/components/decisions/DecisionTimeline';
import { Search, Filter, RefreshCcw, Activity } from 'lucide-react';

export default function DecisionsPage() {
    const [symbol, setSymbol] = useState('TCS');
    const [searchInput, setSearchInput] = useState('TCS');
    const [mode, setMode] = useState<string>('');

    const { data, isLoading, refetch } = useQuery({
        queryKey: ['decisions', symbol, mode],
        queryFn: () => decisionApi.getDecisionsBySymbol(symbol, mode || undefined),
        enabled: !!symbol,
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchInput.trim()) {
            setSymbol(searchInput.trim().toUpperCase());
        }
    };

    return (
        <div className="container mx-auto px-4 py-8 space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Activity className="w-8 h-8 text-blue-600" />
                        Decision Ledger
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">
                        Immutable record of trading decisions with causal explainability
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <form onSubmit={handleSearch} className="relative">
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            placeholder="Enter Symbol (e.g., TCS)"
                            className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none w-64"
                        />
                        <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                    </form>

                    <select
                        value={mode}
                        onChange={(e) => setMode(e.target.value)}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                        <option value="">All Modes</option>
                        <option value="DRY_RUN">Dry Run</option>
                        <option value="LIVE">Live</option>
                        <option value="BACKTEST">Backtest</option>
                    </select>

                    <button
                        onClick={() => refetch()}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        title="Refresh"
                    >
                        <RefreshCcw className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Timeline Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    Decision Timeline: {symbol}
                </h2>
                <DecisionTimeline symbol={symbol} days={30} />
            </div>

            {/* Decisions List */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                        Recent Decisions
                    </h2>
                    <span className="text-sm text-gray-500">
                        Showing last {data?.count || 0} decisions
                    </span>
                </div>

                {isLoading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-48 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
                        ))}
                    </div>
                ) : data?.decisions.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-dashed border-gray-300 dark:border-gray-700">
                        <p className="text-gray-500">No decisions found for {symbol}</p>
                    </div>
                ) : (
                    <div className="grid gap-6">
                        {data?.decisions.map((decision) => (
                            <DecisionCard key={decision.decision_id} decision={decision} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
