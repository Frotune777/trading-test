'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api/analytics';
import { Users, Award, TrendingUp, TrendingDown, LayoutGrid } from 'lucide-react';

export default function PeerComparison({ symbol }: { symbol: string }) {
    const { data: comparison, isLoading } = useQuery({
        queryKey: ['peer-comparison', symbol],
        queryFn: () => analyticsApi.getPeers(symbol),
        enabled: !!symbol,
    });

    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 animate-pulse">
                <div className="h-6 w-1/3 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
                <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} className="h-10 bg-gray-100 dark:bg-gray-700 rounded" />
                    ))}
                </div>
            </div>
        );
    }

    if (!comparison || comparison.error) return null;

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    <h3 className="font-bold text-gray-900 dark:text-white uppercase tracking-wider text-sm">Sector Performance Ranking</h3>
                </div>
                <div className="px-3 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 rounded-full text-[10px] font-black tracking-widest uppercase">
                    {comparison.sector}
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-4 bg-gray-50 dark:bg-gray-900/30 rounded-xl border border-gray-100 dark:border-gray-700/50">
                    <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Sector Rank</p>
                    <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-black text-gray-900 dark:text-white">#{comparison.rank}</span>
                        <span className="text-xs text-gray-400">of {comparison.total_peers}</span>
                    </div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-900/30 rounded-xl border border-gray-100 dark:border-gray-700/50">
                    <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Avg Conviction</p>
                    <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-black text-gray-900 dark:text-white">{Math.round(comparison.avg_sector_conviction)}</span>
                        <span className="text-xs text-gray-400">Group Average</span>
                    </div>
                </div>
            </div>

            {/* Peer List */}
            <div className="space-y-2">
                <div className="grid grid-cols-12 px-2 text-[9px] font-black uppercase tracking-widest text-gray-400 mb-1">
                    <div className="col-span-1">#</div>
                    <div className="col-span-4">SEC. SYMBOL</div>
                    <div className="col-span-4 text-center">CONVICTION</div>
                    <div className="col-span-3 text-right">SIGNAL</div>
                </div>

                {comparison.peers.map((peer, idx) => (
                    <div
                        key={peer.symbol}
                        className={`grid grid-cols-12 items-center px-3 py-3 rounded-lg border transition-all ${peer.is_self
                                ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800 scale-[1.02] shadow-sm z-10'
                                : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30'
                            }`}
                    >
                        <div className="col-span-1 text-xs font-bold text-gray-400">
                            {idx + 1}
                        </div>
                        <div className="col-span-4 flex items-center gap-2">
                            <span className={`font-black tracking-tight ${peer.is_self ? 'text-blue-700 dark:text-blue-400' : 'text-gray-900 dark:text-white'}`}>
                                {peer.symbol}
                            </span>
                            {idx === 0 && <Award className="w-3.5 h-3.5 text-yellow-500" />}
                        </div>
                        <div className="col-span-4">
                            <div className="flex items-center justify-center gap-2">
                                <div className="w-full max-w-[60px] h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${peer.conviction >= 70 ? 'bg-green-500' : peer.conviction <= 30 ? 'bg-red-500' : 'bg-blue-500'}`}
                                        style={{ width: `${peer.conviction}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold w-6">{Math.round(peer.conviction)}</span>
                            </div>
                        </div>
                        <div className="col-span-3 text-right">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-black ${peer.signal === 'BUY' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                    peer.signal === 'SELL' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                        'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                                }`}>
                                {peer.signal}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
