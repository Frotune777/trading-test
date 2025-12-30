'use client';

import { useState } from 'react';
import StrategyList from '@/components/strategy/StrategyList';
import StrategyCodeEditor from '@/components/strategy/StrategyCodeEditor';
import BacktestResults from '@/components/strategy/BacktestResults';
import { type Strategy, type BacktestRequest } from '@/lib/api/strategy';
import { Code2, TrendingUp, ArrowLeft } from 'lucide-react';

type View = 'list' | 'code' | 'backtest';

export default function StrategiesPage() {
    const [currentView, setCurrentView] = useState<View>('list');
    const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
    const [backtestRequest, setBacktestRequest] = useState<BacktestRequest>({
        symbol: 'RELIANCE',
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        initial_capital: 100000,
    });

    const handleViewCode = (strategy: Strategy) => {
        setSelectedStrategy(strategy);
        setCurrentView('code');
    };

    const handleBackToList = () => {
        setCurrentView('list');
        setSelectedStrategy(null);
    };

    const handleRunBacktest = () => {
        if (selectedStrategy) {
            setCurrentView('backtest');
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        {currentView !== 'list' && (
                            <button
                                onClick={handleBackToList}
                                className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg"
                            >
                                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                            </button>
                        )}
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                                {currentView === 'list' && (
                                    <>
                                        <Code2 className="w-8 h-8 text-blue-600" />
                                        Strategy Management
                                    </>
                                )}
                                {currentView === 'code' && (
                                    <>
                                        <Code2 className="w-8 h-8 text-purple-600" />
                                        {selectedStrategy?.name}
                                    </>
                                )}
                                {currentView === 'backtest' && (
                                    <>
                                        <TrendingUp className="w-8 h-8 text-green-600" />
                                        Backtest Results
                                    </>
                                )}
                            </h1>
                            <p className="text-gray-600 dark:text-gray-400 mt-2">
                                {currentView === 'list' && 'Create, edit, and manage your trading strategies'}
                                {currentView === 'code' && 'Edit strategy code and validate implementation'}
                                {currentView === 'backtest' && `Testing ${selectedStrategy?.name} on ${backtestRequest.symbol}`}
                            </p>
                        </div>
                    </div>

                    {currentView === 'code' && (
                        <button
                            onClick={handleRunBacktest}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                        >
                            <TrendingUp className="w-4 h-4" />
                            Run Backtest
                        </button>
                    )}
                </div>

                {/* Content */}
                {currentView === 'list' && (
                    <StrategyList onViewCode={handleViewCode} />
                )}

                {currentView === 'code' && selectedStrategy && (
                    <div className="space-y-6">
                        <StrategyCodeEditor strategyId={selectedStrategy.id} />

                        {/* Backtest Configuration */}
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                                Backtest Configuration
                            </h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Symbol
                                    </label>
                                    <input
                                        type="text"
                                        value={backtestRequest.symbol}
                                        onChange={(e) => setBacktestRequest(prev => ({ ...prev, symbol: e.target.value }))}
                                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Start Date
                                    </label>
                                    <input
                                        type="date"
                                        value={backtestRequest.start_date}
                                        onChange={(e) => setBacktestRequest(prev => ({ ...prev, start_date: e.target.value }))}
                                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        End Date
                                    </label>
                                    <input
                                        type="date"
                                        value={backtestRequest.end_date}
                                        onChange={(e) => setBacktestRequest(prev => ({ ...prev, end_date: e.target.value }))}
                                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Initial Capital
                                    </label>
                                    <input
                                        type="number"
                                        value={backtestRequest.initial_capital}
                                        onChange={(e) => setBacktestRequest(prev => ({ ...prev, initial_capital: Number(e.target.value) }))}
                                        className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {currentView === 'backtest' && selectedStrategy && (
                    <BacktestResults
                        strategyId={selectedStrategy.id}
                        symbol={backtestRequest.symbol}
                        request={backtestRequest}
                    />
                )}
            </div>
        </div>
    );
}
