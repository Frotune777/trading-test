'use client';

import { useQuery } from '@tanstack/react-query';
import { insiderApi } from '@/lib/api/insider';
import { Shield, Brain, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

export default function InsiderSentinel({ symbol }: { symbol: string }) {
    const { data: sentinel, isLoading } = useQuery({
        queryKey: ['insider-sentinel', symbol],
        queryFn: () => insiderApi.getSentinel(symbol),
        enabled: !!symbol,
    });

    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 animate-pulse">
                <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-6" />
                <div className="h-24 bg-gray-100 dark:bg-gray-700 rounded mb-4" />
                <div className="h-4 w-full bg-gray-100 dark:bg-gray-700 rounded" />
            </div>
        );
    }

    if (!sentinel) return null;

    const scoreColor = sentinel.sentinel_score >= 70 ? 'text-green-600' :
        sentinel.sentinel_score <= 30 ? 'text-red-600' :
            'text-blue-600';

    const BiasIcon = sentinel.bias === 'BULLISH' ? TrendingUp :
        sentinel.bias === 'BEARISH' ? TrendingDown : Minus;

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Shield size={120} />
            </div>

            <div className="flex items-center gap-2 mb-6">
                <Shield className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-sm">Insider Sentinel</h3>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-8">
                {/* Score Gauge */}
                <div className="relative flex flex-col items-center">
                    <div className="w-32 h-32 rounded-full border-8 border-gray-100 dark:border-gray-700 flex items-center justify-center relative">
                        <div
                            className="absolute inset-0 rounded-full border-8 border-transparent"
                            style={{
                                borderTopColor: sentinel.sentinel_score >= 50 ? '#10B981' : '#EF4444',
                                transform: `rotate(${(sentinel.sentinel_score / 100) * 360}deg)`,
                                transition: 'transform 1s ease-out'
                            }}
                        />
                        <span className={`text-4xl font-black ${scoreColor}`}>
                            {Math.round(sentinel.sentinel_score)}
                        </span>
                    </div>
                    <span className="text-xs text-gray-500 font-bold mt-2 uppercase tracking-widest text-center">Conviction Score</span>
                </div>

                {/* Status & Signals */}
                <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${sentinel.bias === 'BULLISH' ? 'bg-green-100 text-green-700' :
                                sentinel.bias === 'BEARISH' ? 'bg-red-100 text-red-700' :
                                    'bg-blue-100 text-blue-700'
                            }`}>
                            <BiasIcon className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase">Market Bias</p>
                            <p className="font-bold text-gray-900 dark:text-white">{sentinel.bias}</p>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {sentinel.signals.map((signal, idx) => (
                            <span
                                key={idx}
                                className="px-2 py-1 text-[10px] font-bold uppercase rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600"
                            >
                                {signal}
                            </span>
                        ))}
                    </div>

                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                        <div className="space-y-1">
                            <p className="text-[10px] text-gray-500 uppercase font-bold">Insider Value</p>
                            <p className="text-sm font-bold text-gray-900 dark:text-white">₹{sentinel.metrics.net_insider_value} Cr</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-[10px] text-gray-500 uppercase font-bold">Block Qty</p>
                            <p className="text-sm font-bold text-gray-900 dark:text-white">{sentinel.metrics.block_deal_qty}</p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-[10px] text-gray-500 uppercase font-bold">Short Int.</p>
                            <p className={`text-sm font-bold ${sentinel.metrics.short_selling_pct > 5 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
                                {sentinel.metrics.short_selling_pct.toFixed(1)}%
                            </p>
                        </div>
                        <div className="space-y-1">
                            <p className="text-[10px] text-gray-500 uppercase font-bold">Cluster</p>
                            <p className="text-sm font-bold text-gray-900 dark:text-white">{sentinel.metrics.insider_buys} Buys</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-4 flex items-start gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/10 rounded-lg border border-indigo-100 dark:border-indigo-900/30">
                <Info className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                <p className="text-[11px] text-indigo-700 dark:text-indigo-400 italic">
                    Sentinel correlates insider trades, bulk deals, and short inventory to detect smart money footprints before moves materialise.
                </p>
            </div>
        </div>
    );
}
