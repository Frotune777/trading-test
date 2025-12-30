'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BacktestResponse } from '@/lib/api/strategy-api';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Legend, AreaChart, Area
} from 'recharts';
import { TrendingUp, TrendingDown, Info, Calculator, Download, Table, AlertCircle } from 'lucide-react';

interface BacktestResultsProps {
    results: BacktestResponse;
}

const BacktestResults: React.FC<BacktestResultsProps> = ({ results }) => {
    if (results.error) {
        return (
            <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-3 rounded flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                {results.error}
            </div>
        );
    }

    const returnPct = ((results.final_capital - 100000) / 100000 * 100);
    const isProfit = returnPct >= 0;

    // Format equity curve for Recharts
    const chartData = results.equity_curve.map((point) => ({
        ...point,
        date: new Date(point.date).toLocaleDateString(),
        // Calculate drawdown for each point
        // Note: In a real app we'd pre-calculate this or do it more efficiently
    }));

    // Calculate drawdown curve
    let peak = 100000;
    const drawdownData = results.equity_curve.map((point) => {
        if (point.value > peak) peak = point.value;
        const dd = ((peak - point.value) / peak) * 100;
        return {
            date: new Date(point.date).toLocaleDateString(),
            drawdown: -dd // Negative for visualization
        };
    });

    const exportToCSV = () => {
        const headers = ['Timestamp', 'Action', 'Price', 'PnL', 'PnL %'];
        const csvRows = results.trades.map(t => [
            t.exit_timestamp || t.timestamp,
            t.action,
            t.price,
            t.pnl || 0,
            t.pnl_pct || 0
        ].join(','));

        const csvContent = [headers.join(','), ...csvRows].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `backtest_${results.symbol}_${new Date().toISOString()}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                    label="Return"
                    value={`${returnPct.toFixed(2)}%`}
                    subValue={`₹${(results.final_capital - 100000).toLocaleString()}`}
                    status={isProfit ? 'success' : 'danger'}
                />
                <MetricCard
                    label="Sharpe Ratio"
                    value={results.sharpe.toFixed(2)}
                    subValue="Risk-adjusted return"
                    status={results.sharpe > 1 ? 'success' : results.sharpe > 0 ? 'warning' : 'danger'}
                />
                <MetricCard
                    label="Max Drawdown"
                    value={`${results.max_drawdown.toFixed(2)}%`}
                    subValue="Peak to trough decline"
                    status={results.max_drawdown < 10 ? 'success' : results.max_drawdown < 20 ? 'warning' : 'danger'}
                />
                <MetricCard
                    label="Win Rate"
                    value={`${(results.total_trades > 0 ? (results.trades.filter(t => (t.pnl || 0) > 0).length / results.total_trades * 100) : 0).toFixed(1)}%`}
                    subValue={`${results.total_trades} total trades`}
                    status="info"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                    label="Sortino"
                    value={results.sortino.toFixed(2)}
                    subValue="Downside risk-adjusted"
                    status="info"
                />
                <MetricCard
                    label="Calmar"
                    value={results.calmar.toFixed(2)}
                    subValue="Ann. return / Max DD"
                    status="info"
                />
                <MetricCard
                    label="Final Capital"
                    value={`₹${results.final_capital.toLocaleString()}`}
                    subValue="At test completion"
                    status="info"
                />
            </div>

            {/* Equity Curve Chart */}
            <Card className="bg-slate-950 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Equity Curve</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis
                                    dataKey="date"
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    fontSize={12}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}
                                    itemStyle={{ color: '#60a5fa' }}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    name="Equity"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Drawdown Chart */}
            <Card className="bg-slate-950 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Drawdown (%)</CardTitle>
                    <TrendingDown className="h-4 w-4 text-red-500" />
                </CardHeader>
                <CardContent>
                    <div className="h-[150px] w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={drawdownData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" hide />
                                <YAxis
                                    stroke="#94a3b8"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    domain={[-25, 0]}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}
                                    itemStyle={{ color: '#ef4444' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="drawdown"
                                    name="Drawdown"
                                    stroke="#ef4444"
                                    fill="#ef4444"
                                    fillOpacity={0.2}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Trade Log Table */}
            <Card className="bg-slate-950 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-2">
                        <Table className="h-4 w-4 text-muted-foreground" />
                        <CardTitle className="text-sm font-medium">Execution Log</CardTitle>
                    </div>
                    <button
                        onClick={exportToCSV}
                        className="p-2 hover:bg-slate-800 rounded-lg text-blue-400 flex items-center gap-2 text-xs"
                    >
                        <Download className="w-3 h-3" />
                        Export CSV
                    </button>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto pt-4">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-slate-800 text-slate-500">
                                    <th className="text-left pb-3 font-medium">Date/Time</th>
                                    <th className="text-left pb-3 font-medium">Action</th>
                                    <th className="text-right pb-3 font-medium">Price</th>
                                    <th className="text-right pb-3 font-medium">PnL</th>
                                    <th className="text-right pb-3 font-medium">PnL %</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {results.trades.map((trade, idx) => (
                                    <tr key={idx} className="hover:bg-slate-900/50 transition-colors">
                                        <td className="py-3 text-slate-300">
                                            {new Date(trade.exit_timestamp || trade.timestamp).toLocaleString()}
                                        </td>
                                        <td className="py-3">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${trade.action.includes('BUY') || trade.action.includes('SHORT')
                                                    ? 'bg-blue-900/50 text-blue-400 border border-blue-500/20'
                                                    : 'bg-orange-900/50 text-orange-400 border border-orange-500/20'
                                                }`}>
                                                {trade.action}
                                            </span>
                                        </td>
                                        <td className="py-3 text-right font-mono">₹{trade.price.toFixed(2)}</td>
                                        <td className={`py-3 text-right font-medium ${(trade.pnl || 0) > 0 ? 'text-green-400' : 'text-red-400'
                                            }`}>
                                            {trade.pnl ? `₹${trade.pnl.toLocaleString()}` : '-'}
                                        </td>
                                        <td className={`py-3 text-right font-medium ${(trade.pnl_pct || 0) > 0 ? 'text-green-400' : 'text-red-400'
                                            }`}>
                                            {trade.pnl_pct ? `${trade.pnl_pct.toFixed(2)}%` : '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

interface MetricCardProps {
    label: string;
    value: string | number;
    subValue: string;
    status: 'success' | 'danger' | 'warning' | 'info';
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, subValue, status }) => {
    const statusColors = {
        success: 'text-green-500',
        danger: 'text-red-500',
        warning: 'text-yellow-500',
        info: 'text-blue-500'
    };

    return (
        <Card className="bg-slate-950 border-slate-800 hover:border-slate-700 transition-colors">
            <CardContent className="pt-6">
                <div className="flex flex-col gap-1">
                    <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">{label}</span>
                    <span className={`text-2xl font-bold ${statusColors[status]}`}>{value}</span>
                    <span className="text-[10px] text-slate-600 font-medium truncate">{subValue}</span>
                </div>
            </CardContent>
        </Card>
    );
};

export default BacktestResults;
