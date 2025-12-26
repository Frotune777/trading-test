'use client';

import { useEffect, useState } from 'react';
import { quadAnalyticsAPI, SignalAccuracyMetrics } from '@/lib/api/quad-analytics-api';
import { TrendingUp, TrendingDown, Target, Activity } from 'lucide-react';

interface PerformanceTrackerProps {
  symbol: string;
  days?: number;
}

export default function PerformanceTracker({ symbol, days = 90 }: PerformanceTrackerProps) {
  const [metrics, setMetrics] = useState<SignalAccuracyMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, [symbol, days]);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const data = await quadAnalyticsAPI.getSignalAccuracy(symbol, days);
      setMetrics(data);
    } catch (error) {
      console.error('Error loading performance metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  if (!metrics || metrics.total_signals === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Target className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No signal history available</p>
        <p className="text-sm mt-1">Signals need time to be evaluated</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1 tracking-tight">Total Signals</div>
          <div className="text-2xl font-mono font-bold text-slate-200">{metrics.total_signals}</div>
          <div className="text-[9px] text-slate-600 mt-1 uppercase font-mono tracking-tighter">Evaluation period: {days}d</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1 tracking-tight">Win Rate</div>
          <div className={cn(
             "text-2xl font-mono font-bold",
             metrics.win_rate >= 60 ? 'text-emerald-500' : 'text-rose-500'
          )}>
            {metrics.win_rate.toFixed(1)}%
          </div>
          <div className="text-[9px] text-slate-600 mt-1 uppercase font-mono tracking-tighter">{metrics.correct_signals} VALID ENTRIES</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1 tracking-tight">Correct / Total</div>
          <div className="text-2xl font-mono font-bold text-slate-200">{metrics.correct_signals} / {metrics.total_signals}</div>
          <div className="text-[9px] text-slate-600 mt-1 uppercase font-mono tracking-tighter">Signal Accuracy Metric</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-4 rounded-lg shadow-sm">
          <div className="text-[10px] uppercase font-bold text-slate-500 mb-1 tracking-tight">Net Accuracy P/L</div>
          <div className={cn(
             "text-2xl font-mono font-bold",
             metrics.total_profit_loss >= 0 ? 'text-emerald-500' : 'text-rose-500'
          )}>
            {metrics.total_profit_loss >= 0 ? '+' : ''}{metrics.total_profit_loss.toFixed(2)}
          </div>
          <div className="text-[9px] text-slate-600 mt-1 uppercase font-mono tracking-tighter">Points across {metrics.total_signals} signals</div>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-lg p-5 shadow-sm">
        <h4 className="text-[12px] font-black uppercase text-slate-400 mb-4 tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-500" />
          Conviction Precision Analysis
        </h4>
        <div className="grid grid-cols-2 gap-8">
          <div className="space-y-1">
            <div className="text-[10px] uppercase font-bold text-slate-600">Avg Conviction (Winning)</div>
            <div className="flex items-center gap-3">
              <div className="text-2xl font-mono font-black text-emerald-400">{metrics.avg_conviction_winning.toFixed(1)}%</div>
              <div className="h-1 flex-1 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: `${metrics.avg_conviction_winning}%` }}></div>
              </div>
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-[10px] uppercase font-bold text-slate-600">Avg Conviction (Losing)</div>
            <div className="flex items-center gap-3">
              <div className="text-2xl font-mono font-black text-rose-400">{metrics.avg_conviction_losing.toFixed(1)}%</div>
              <div className="h-1 flex-1 bg-slate-900 rounded-full overflow-hidden">
                <div className="h-full bg-rose-500" style={{ width: `${metrics.avg_conviction_losing}%` }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metrics.best_signal && (
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-4">
            <h4 className="text-[10px] font-black text-emerald-500 uppercase mb-3 tracking-widest flex items-center gap-2">
              <TrendingUp className="w-3 h-3" /> Peak Alpha Signal
            </h4>
            <div className="grid grid-cols-2 gap-y-2 text-[11px]">
              <div className="text-slate-500">Execution Date</div>
              <div className="text-right font-mono text-emerald-100">{new Date(metrics.best_signal.date).toLocaleDateString()}</div>
              
              <div className="text-slate-500">Bias / Conviction</div>
              <div className="text-right font-mono text-emerald-100">{metrics.best_signal.signal} @ {metrics.best_signal.conviction}%</div>
              
              <div className="text-slate-500 font-bold">Signal Return</div>
              <div className="text-right font-mono font-bold text-emerald-400">+{metrics.best_signal.profit_loss.toFixed(2)} pts</div>
            </div>
          </div>
        )}

        {metrics.worst_signal && (
          <div className="bg-rose-500/5 border border-rose-500/20 rounded-lg p-4">
            <h4 className="text-[10px] font-black text-rose-500 uppercase mb-3 tracking-widest flex items-center gap-2">
              <TrendingDown className="w-3 h-3" /> Max Drawdown Signal
            </h4>
            <div className="grid grid-cols-2 gap-y-2 text-[11px]">
              <div className="text-slate-500">Execution Date</div>
              <div className="text-right font-mono text-rose-100">{new Date(metrics.worst_signal.date).toLocaleDateString()}</div>
              
              <div className="text-slate-500">Bias / Conviction</div>
              <div className="text-right font-mono text-rose-100">{metrics.worst_signal.signal} @ {metrics.worst_signal.conviction}%</div>
              
              <div className="text-slate-500 font-bold">Signal Loss</div>
              <div className="text-right font-mono font-bold text-rose-400">{metrics.worst_signal.profit_loss.toFixed(2)} pts</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
