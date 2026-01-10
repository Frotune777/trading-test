'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Play, Loader2, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import StrategyEditor from '@/components/strategy/StrategyEditor';
import BacktestResults from '@/components/strategy/BacktestResults';
import { strategyAPI, BacktestRequest, BacktestResponse, ValidationResult } from '@/lib/api/strategy-api';

export default function StrategyDetailPage() {
    const params = useParams();
    const router = useRouter();
    const strategyId = parseInt(params.id as string);

    const [strategy, setStrategy] = useState<any>(null);
    const [code, setCode] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Backtest state
    const [showBacktest, setShowBacktest] = useState(false);
    const [backtestSymbol, setBacktestSymbol] = useState('RELIANCE');
    const [backtestRunning, setBacktestRunning] = useState(false);
    const [backtestResults, setBacktestResults] = useState<BacktestResponse | null>(null);
    const [backtestCapital, setBacktestCapital] = useState(100000);
    const [backtestSlippage, setBacktestSlippage] = useState(0.1); // in percent
    const [backtestCommission, setBacktestCommission] = useState(20); // fixed


    useEffect(() => {
        loadStrategy();
    }, [strategyId]);

    const loadStrategy = async () => {
        try {
            setLoading(true);
            const [strategyData, codeData] = await Promise.all([
                strategyAPI.getStrategy(strategyId),
                strategyAPI.getStrategyCode(strategyId)
            ]);

            setStrategy(strategyData);
            setCode(codeData.code);
            setError(null);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveCode = async (newCode: string) => {
        try {
            await strategyAPI.updateStrategyCode(strategyId, newCode);
            setCode(newCode);
        } catch (err: any) {
            throw new Error(`Failed to save code: ${err.message}`);
        }
    };

    const handleValidateCode = async (codeToValidate: string): Promise<ValidationResult> => {
        try {
            return await strategyAPI.validateCode(codeToValidate);
        } catch (err: any) {
            throw new Error(`Validation failed: ${err.message}`);
        }
    };

    const handleRunBacktest = async () => {
        if (!backtestSymbol) {
            alert('Please enter a symbol');
            return;
        }

        setBacktestRunning(true);
        try {
            const request: BacktestRequest = {
                symbol: backtestSymbol,
                initial_capital: backtestCapital,
                slippage_pct: backtestSlippage / 100,
                commission_fixed: backtestCommission
            };

            const results = await strategyAPI.backtestStrategy(strategyId, request);
            setBacktestResults(results);
        } catch (err: any) {
            alert(`Backtest failed: ${err.message}`);
        } finally {
            setBacktestRunning(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => router.push('/strategies')}
                    className="p-2 hover:bg-slate-800 rounded-lg"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-3xl font-bold">{strategy?.name}</h1>
                    <p className="text-muted-foreground">
                        {strategy?.platform} • {strategy?.is_active ? 'Active' : 'Inactive'}
                    </p>
                </div>
            </div>

            {/* Strategy Info */}
            <Card>
                <CardHeader>
                    <CardTitle>Strategy Details</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Trading Mode</p>
                            <p className="font-medium">{strategy?.trading_mode}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Type</p>
                            <p className="font-medium">{strategy?.is_intraday ? 'Intraday' : 'Positional'}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Symbols</p>
                            <p className="font-medium">{strategy?.symbol_count}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Status</p>
                            <p className={`font-medium ${strategy?.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                                {strategy?.is_active ? 'Active' : 'Inactive'}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Code Editor */}
            <StrategyEditor
                strategyId={strategyId}
                initialCode={code}
                onSave={handleSaveCode}
                onValidate={handleValidateCode}
            />

            {/* Backtest Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="w-5 h-5" />
                        Backtest Strategy
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium uppercase">Symbol</label>
                            <input
                                type="text"
                                value={backtestSymbol}
                                onChange={(e) => setBacktestSymbol(e.target.value)}
                                placeholder="e.g. RELIANCE"
                                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium uppercase">Capital (₹)</label>
                            <input
                                type="number"
                                value={backtestCapital}
                                onChange={(e) => setBacktestCapital(Number(e.target.value))}
                                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium uppercase">Slippage (%)</label>
                            <input
                                type="number"
                                step="0.01"
                                value={backtestSlippage}
                                onChange={(e) => setBacktestSlippage(Number(e.target.value))}
                                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                            />
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-xs text-slate-500 font-medium uppercase">Comm. (₹/side)</label>
                            <input
                                type="number"
                                value={backtestCommission}
                                onChange={(e) => setBacktestCommission(Number(e.target.value))}
                                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <button
                            onClick={handleRunBacktest}
                            disabled={backtestRunning}
                            className="flex items-center gap-2 px-8 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-bold transition-all shadow-lg shadow-blue-500/20"
                        >
                            {backtestRunning ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Running Simulation...
                                </>
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Run Backtest 2.0
                                </>
                            )}
                        </button>
                    </div>

                    {/* Backtest Results */}
                    {backtestResults && <BacktestResults results={backtestResults} />}

                </CardContent>
            </Card>
        </div>
    );
}
