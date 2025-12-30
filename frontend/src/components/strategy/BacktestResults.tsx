'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { strategyApi, type BacktestResult, type BacktestRequest } from '@/lib/api/strategy';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Download } from 'lucide-react';

interface BacktestResultsProps {
    strategyId: number;
    symbol: string;
    request: BacktestRequest;
}

export default function BacktestResults({ strategyId, symbol, request }: BacktestResultsProps) {
    const { data, isLoading, error } = useQuery<BacktestResult>({
        queryKey: ['backtest', strategyId, symbol, request],
        queryFn: () => strategyApi.backtest(strategyId, request),
        enabled: !!strategyId && !!symbol,
    });

    const exportToCSV = () => {
        if (!data?.trades) return;

        const headers = ['Entry Date', 'Exit Date', 'Signal', 'P&L', 'P&L %'];
        const rows = data.trades.map(trade => [
            trade.entry_date,
            trade.exit_date,
            trade.signal,
            trade.pnl.toFixed(2),
            trade.pnl_pct.toFixed(2),
        ]);

        const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `backtest_${symbol}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    if (isLoading) {
        return (
            <div className="w-full h-96 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Running backtest...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full h-96 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <p className="text-red-600 dark:text-red-400">Failed to run backtest</p>
            </div>
        );
    }

    if (!data) return null;

    if (data.error) {
        return (
            <div className="w-full p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <p className="text-yellow-800 dark:text-yellow-200">{data.error}</p>
            </div>
        );
    }

    const totalReturn = ((data.final_capital - (request.initial_capital || 100000)) / (request.initial_capital || 100000)) * 100;
    const winningTrades = data.trades.filter(t => t.pnl > 0).length;
    const winRate = data.total_trades > 0 ? (winningTrades / data.total_trades) * 100 : 0;

    return (
        <div className="w-full space-y-6">
            {/* Performance Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Total Return</p>
                    <p className={`text-2xl font-bold ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        ₹{data.final_capital.toLocaleString()}
                    </p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {data.sharpe.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Risk-adjusted return</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</p>
                    <p className="text-2xl font-bold text-red-600">
                        {data.max_drawdown.toFixed(2)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Peak to trough</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Win Rate</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                        {winRate.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        {winningTrades}/{data.total_trades} trades
                    </p>
                </div>
            </div>

            {/* Additional Metrics */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Sortino Ratio</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {data.sortino.toFixed(2)}
                    </p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Calmar Ratio</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                        {data.calmar.toFixed(2)}
                    </p>
                </div>
            </div>

            {/* Equity Curve */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Equity Curve
                    </h3>
                </div>
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={data.equity_curve}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="date"
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                        />
                        <YAxis
                            stroke="#9CA3AF"
                            tick={{ fill: '#9CA3AF' }}
                            tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '0.5rem'
                            }}
                            labelStyle={{ color: '#F3F4F6' }}
                            formatter={(value: number) => [`₹${value.toLocaleString()}`, 'Equity']}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#10B981"
                            strokeWidth={2}
                            dot={false}
                            name="Portfolio Value"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Trade List */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Recent Trades
                    </h3>
                    <button
                        onClick={exportToCSV}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    >
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 dark:text-gray-300">Entry</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 dark:text-gray-300">Exit</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 dark:text-gray-300">Signal</th>
                                <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 dark:text-gray-300">P&L</th>
                                <th className="px-4 py-2 text-right text-xs font-medium text-gray-600 dark:text-gray-300">P&L %</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {data.trades.slice(0, 20).map((trade, i) => (
                                <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">
                                        {new Date(trade.entry_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-4 py-2 text-sm text-gray-900 dark:text-white">
                                        {new Date(trade.exit_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-4 py-2">
                                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${trade.signal === 'BUY'
                                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                                : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                            }`}>
                                            {trade.signal === 'BUY' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                            {trade.signal}
                                        </span>
                                    </td>
                                    <td className={`px-4 py-2 text-sm text-right font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                        {trade.pnl >= 0 ? '+' : ''}₹{trade.pnl.toLocaleString()}
                                    </td>
                                    <td className={`px-4 py-2 text-sm text-right font-medium ${trade.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                        {trade.pnl_pct >= 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
