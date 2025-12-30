'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsApi, PillarWeights } from '@/lib/api/analytics';
import { Settings, Save, RotateCcw, AlertCircle, Info } from 'lucide-react';
import toast from 'react-hot-toast';

export default function PillarWeightConfig() {
    const queryClient = useQueryClient();
    const [weights, setWeights] = useState<PillarWeights | null>(null);

    const { data: serverWeights, isLoading } = useQuery({
        queryKey: ['pillar-weights'],
        queryFn: analyticsApi.getWeights,
    });

    useEffect(() => {
        if (serverWeights) {
            setWeights(serverWeights);
        }
    }, [serverWeights]);

    const updateMutation = useMutation({
        mutationFn: (newWeights: PillarWeights) => analyticsApi.setWeights(newWeights),
        onSuccess: () => {
            toast.success('Pillar weights updated successfully');
            queryClient.invalidateQueries({ queryKey: ['pillar-weights'] });
        },
        onError: (err: any) => toast.error(`Update failed: ${err.message}`)
    });

    const resetMutation = useMutation({
        mutationFn: analyticsApi.resetWeights,
        onSuccess: () => {
            toast.success('Weights reset to default');
            queryClient.invalidateQueries({ queryKey: ['pillar-weights'] });
        }
    });

    if (isLoading || !weights) {
        return <div className="h-64 bg-gray-50 dark:bg-gray-800 rounded-xl animate-pulse" />;
    }

    const handleSliderChange = (pillar: keyof PillarWeights, value: number) => {
        setWeights(prev => prev ? { ...prev, [pillar]: value / 100 } : null);
    };

    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    const isValid = Math.abs(total - 1.0) < 0.001;

    const PILLARS = [
        { key: 'trend', label: 'Trend Pillar', color: 'bg-blue-500', desc: 'Price orientation and structure' },
        { key: 'momentum', label: 'Momentum Pillar', color: 'bg-green-500', desc: 'Velocity and relative strength' },
        { key: 'volatility', label: 'Volatility Pillar', color: 'bg-yellow-500', desc: 'Risk and noise levels' },
        { key: 'liquidity', label: 'Liquidity Pillar', color: 'bg-purple-500', desc: 'Volume and transaction ease' },
        { key: 'sentiment', label: 'Sentiment Pillar', color: 'bg-pink-500', desc: 'Social and market psychological bias' },
        { key: 'regime', label: 'Regime Pillar', color: 'bg-indigo-500', desc: 'Macro market environment state' },
    ];

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-2">
                    <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <h3 className="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-sm">Conviction Calculation Weights</h3>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => resetMutation.mutate()}
                        className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        title="Reset to Defaults"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => updateMutation.mutate(weights)}
                        disabled={!isValid || updateMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-bold text-xs uppercase tracking-widest"
                    >
                        <Save className="w-4 h-4" />
                        Save Changes
                    </button>
                </div>
            </div>

            <div className="space-y-6">
                {PILLARS.map((p) => (
                    <div key={p.key} className="space-y-2">
                        <div className="flex justify-between items-baseline">
                            <div>
                                <span className="text-[11px] font-black text-gray-900 dark:text-white uppercase tracking-wider">{p.label}</span>
                                <p className="text-[10px] text-gray-400 italic">{p.desc}</p>
                            </div>
                            <span className="text-sm font-black text-gray-900 dark:text-white">
                                {Math.round(weights[p.key as keyof PillarWeights] * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            step="5"
                            value={Math.round(weights[p.key as keyof PillarWeights] * 100)}
                            onChange={(e) => handleSliderChange(p.key as keyof PillarWeights, parseInt(e.target.value))}
                            className={`w-full h-1.5 rounded-lg appearance-none cursor-pointer accent-indigo-600 bg-gray-100 dark:bg-gray-700`}
                        />
                    </div>
                ))}
            </div>

            <div className={`mt-8 p-4 rounded-xl border flex items-center justify-between ${isValid ? 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800' : 'bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-800'
                }`}>
                <div className="flex items-center gap-3">
                    {isValid ? (
                        <div className="p-2 bg-green-100 dark:bg-green-800 rounded-full">
                            <Info className="w-4 h-4 text-green-600 dark:text-green-300" />
                        </div>
                    ) : (
                        <div className="p-2 bg-red-100 dark:bg-red-800 rounded-full">
                            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-300" />
                        </div>
                    )}
                    <div>
                        <p className={`text-xs font-bold ${isValid ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>
                            Current Total Weight: {Math.round(total * 100)}%
                        </p>
                        {!isValid && (
                            <p className="text-[10px] text-red-600 dark:text-red-400">Weights must sum exactly to 100% to save.</p>
                        )}
                    </div>
                </div>
                {!isValid && (
                    <button
                        onClick={() => {
                            // Simple auto-balancer: find current total and adjust regime as a proxy for balance
                            const currentSum = Object.values(weights).reduce((a, b) => a + b, 0);
                            const diff = 1.0 - currentSum;
                            setWeights(prev => prev ? { ...prev, regime: Math.max(0, prev.regime + diff) } : null);
                        }}
                        className="text-[10px] font-black uppercase text-red-700 dark:text-red-400 hover:underline"
                    >
                        Auto-Balance
                    </button>
                )}
            </div>
        </div>
    );
}
