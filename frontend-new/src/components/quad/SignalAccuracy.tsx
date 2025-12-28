'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Target, TrendingUp, TrendingDown, Percent, Award, AlertTriangle, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import { marketAPI } from '@/lib/api/market-api';
import { Loader2 } from 'lucide-react';
import api from '@/lib/api/client';

interface SignalAccuracyProps {
  symbol: string;
}

function ClientDate({ date }: { date: string }) {
  const [formatted, setFormatted] = useState<string>('');
  useEffect(() => {
    setFormatted(new Date(date).toLocaleDateString());
  }, [date]);
  return <span>{formatted || '...'}</span>;
}

export default function SignalAccuracy({ symbol }: SignalAccuracyProps) {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAccuracy() {
      if (!symbol) return;
      try {
        setLoading(true);
        const response = await api.get(`/quad/${symbol}/accuracy`);
        setMetrics(response.data);
      } catch (err) {
        console.error('Failed to load signal accuracy', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAccuracy();
  }, [symbol]);

  if (loading) {
    return (
      <Card className="bg-card border-border h-[300px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </Card>
    );
  }

  if (!metrics || metrics.total_signals === 0) {
    return (
      <Card className="bg-card border-border h-[300px] flex flex-col items-center justify-center p-6 text-center">
         <div className="p-3 bg-muted/20 rounded-full border border-border mb-4">
           <ShieldCheck className="w-8 h-8 text-muted-foreground" />
         </div>
         <h4 className="text-muted-foreground font-bold mb-1 uppercase tracking-wider text-sm">Accuracy Baseline Pending</h4>
         <p className="text-muted-foreground/60 text-[11px] max-w-xs mx-auto italic">
           Waiting for signal evaluation cycles to complete for {symbol}. 
           Evaluation typically occurs 5 days after signal issuance.
         </p>
      </Card>
    );
  }

  const winRate = metrics.win_rate;
  const isHealthy = winRate >= 60;

  return (
    <Card className="bg-card border-border overflow-hidden shadow-2xl">
      <CardHeader className="py-2 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground font-black flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-primary" />
            Signal Accuracy Analysis
          </CardTitle>
          <div className={cn(
            "text-[8px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-tighter",
            isHealthy ? "bg-success/10 text-success border-success/20" : "bg-warning/10 text-warning border-warning/20"
          )}>
            {isHealthy ? 'High Precision' : 'Calibration Req.'}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {/* Main Stats Row */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-muted/10 border border-border rounded-lg p-2.5 flex flex-col items-center justify-center">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Win Rate</span>
            <span className={cn(
              "text-xl font-black tabular-nums",
              winRate >= 70 ? "text-success" : winRate >= 50 ? "text-warning" : "text-destructive"
            )}>
              {winRate.toFixed(1)}%
            </span>
          </div>
          <div className="bg-muted/10 border border-border rounded-lg p-2.5 flex flex-col items-center justify-center">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest mb-0.5">Total</span>
            <span className="text-xl font-black tabular-nums text-foreground">
              {metrics.total_signals}
            </span>
          </div>
        </div>

        {/* Conviction Gap */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Conviction Calibration</span>
            <span className="text-[8px] text-muted-foreground font-mono">WIN VS LOSS</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden flex">
            <div 
              className="h-full bg-success opacity-80" 
              style={{ width: `${(metrics.avg_conviction_winning / (metrics.avg_conviction_winning + metrics.avg_conviction_losing)) * 100}%` }} 
            />
            <div 
              className="h-full bg-destructive opacity-40" 
              style={{ width: `${(metrics.avg_conviction_losing / (metrics.avg_conviction_winning + metrics.avg_conviction_losing)) * 100}%` }} 
            />
          </div>
          <div className="flex justify-between text-[8px] font-bold font-mono">
            <span className="text-success">{metrics.avg_conviction_winning.toFixed(0)}%</span>
            <span className="text-destructive">{metrics.avg_conviction_losing.toFixed(0)}%</span>
          </div>
        </div>

        {/* Best/Worst Signal Section */}
        <div className="grid grid-cols-1 gap-3">
          {metrics.best_signal && (
            <div className="flex items-center justify-between p-3 rounded-lg border border-success/20 bg-success/5">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-success/20 rounded-md">
                   <Award className="w-4 h-4 text-success" />
                </div>
                <div>
                  <div className="text-[10px] text-success font-black uppercase tracking-widest">Best Performer</div>
                  <div className="text-[11px] text-muted-foreground"><ClientDate date={metrics.best_signal.date} /></div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-black text-success tabular-nums">+₹{metrics.best_signal.profit_loss.toFixed(2)}</div>
                <div className="text-[9px] text-muted-foreground font-mono">{metrics.best_signal.conviction}% CONV</div>
              </div>
            </div>
          )}

          {metrics.worst_signal && (
            <div className="flex items-center justify-between p-3 rounded-lg border border-destructive/20 bg-destructive/5">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-destructive/20 rounded-md">
                   <AlertTriangle className="w-4 h-4 text-destructive" />
                </div>
                <div>
                  <div className="text-[10px] text-destructive font-black uppercase tracking-widest">Least Correct</div>
                  <div className="text-[11px] text-muted-foreground"><ClientDate date={metrics.worst_signal.date} /></div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-black text-destructive tabular-nums">-₹{Math.abs(metrics.worst_signal.profit_loss).toFixed(2)}</div>
                <div className="text-[9px] text-muted-foreground font-mono">{metrics.worst_signal.conviction}% CONV</div>
              </div>
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-border flex items-center justify-between">
           <span className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Evaluated P&L (Simulated)</span>
           <span className={cn(
             "text-xs font-black tabular-nums",
             metrics.total_profit_loss >= 0 ? "text-success" : "text-destructive"
           )}>
             {metrics.total_profit_loss >= 0 ? '+' : ''}₹{metrics.total_profit_loss.toFixed(2)}
           </span>
        </div>

        {/* Rolling Accuracy */}
        <div className="grid grid-cols-3 gap-2 pt-2">
           {['7d', '30d', '90d'].map((period) => (
             <div key={period} className="text-center p-2 rounded bg-muted/20 border border-border/50">
               <div className="text-[8px] text-muted-foreground uppercase font-black">{period} Score</div>
               <div className={cn(
                 "text-xs font-black",
                 metrics.rolling_win_rates?.[period] >= 70 ? "text-success" : 
                 metrics.rolling_win_rates?.[period] >= 50 ? "text-warning" : "text-destructive"
               )}>
                 {metrics.rolling_win_rates?.[period]?.toFixed(0) || 0}%
               </div>
             </div>
           ))}
        </div>
      </CardContent>
    </Card>
  );
}
