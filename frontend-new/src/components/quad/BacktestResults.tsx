'use client';

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Activity, TrendingUp, TrendingDown, Target, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { QuadService } from '@/lib/api/quad';

interface BacktestResultsProps {
  symbol: string;
}

export default function BacktestResults({ symbol }: BacktestResultsProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simulationId, setSimulationId] = useState<string>('');

  useEffect(() => {
    setSimulationId(Math.random().toString(36).substring(7).toUpperCase());
    async function fetchBacktest() {
      if (!symbol) return;
      try {
        setLoading(true);
        setError(null);
        const response = await QuadService.getBacktest(symbol);
        setData(response);
      } catch (err: any) {
        console.error('Failed to load backtest data', err);
        setError('Market data sync pending for this instrument.');
      } finally {
        setLoading(false);
      }
    }
    fetchBacktest();
  }, [symbol]);

  if (loading) {
    return (
      <Card className="bg-card border-border h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </Card>
    );
  }

  if (error || !data || data.total_trades === 0) {
    return (
      <Card className="bg-card border-border overflow-hidden shadow-2xl">
        <CardContent className="h-[400px] flex flex-col items-center justify-center p-6 text-center">
          <div className="p-3 bg-muted/20 rounded-full border border-border mb-4">
            <Activity className="w-8 h-8 text-muted-foreground" />
          </div>
          <h4 className="text-muted-foreground font-bold mb-1 uppercase tracking-wider text-sm">Equity Simulation Delayed</h4>
          <p className="text-muted-foreground/60 text-[11px] max-w-xs mx-auto italic">
            {error || `Insufficient valid QUAD signals for ${symbol} to generate a statistically significant equity curve.`}
          </p>
        </CardContent>
      </Card>
    );
  }

  const isProfitable = data.avg_return > 0;

  return (
    <Card className="bg-card border-border overflow-hidden shadow-2xl">
      <CardHeader className="py-2 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[9px] uppercase tracking-widest text-muted-foreground font-black flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-primary" />
            Equity Curve Simulation
          </CardTitle>
          <div className={cn(
            "text-[8px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-tighter",
            isProfitable ? "bg-success/10 text-success border-success/20" : "bg-destructive/10 text-destructive border-destructive/20"
          )}>
            {isProfitable ? 'Alpha+' : 'Alpha-'}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {/* Main Stats Row */}
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-muted/10 border border-border rounded-lg p-2">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest block mb-0.5">Win Rate</span>
            <span className="text-base font-black tabular-nums text-foreground">{(data.win_rate ?? 0).toFixed(1)}%</span>
          </div>
          <div className="bg-muted/10 border border-border rounded-lg p-2">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest block mb-0.5">Avg Ret</span>
            <span className={cn(
              "text-base font-black tabular-nums",
              data.avg_return >= 0 ? "text-success" : "text-destructive"
            )}>{(data.avg_return ?? 0).toFixed(2)}%</span>
          </div>
          <div className="bg-muted/10 border border-border rounded-lg p-2">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest block mb-0.5">Trades</span>
            <span className="text-base font-black tabular-nums text-foreground">{data.total_trades}</span>
          </div>
          <div className="bg-muted/10 border border-border rounded-lg p-2">
            <span className="text-[8px] text-muted-foreground uppercase font-black tracking-widest block mb-0.5">DD</span>
            <span className="text-base font-black tabular-nums text-destructive">-{(data.max_drawdown ?? 0).toFixed(1)}%</span>
          </div>
        </div>

        {/* Equity Curve Chart */}
        <div className="h-48 pt-2 min-w-0 min-h-[192px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.equity_curve}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="var(--muted-foreground)"
                fontSize={8}
                tickFormatter={(val) => val.split('-').slice(1).join('/')}
              />
              <YAxis
                stroke="var(--muted-foreground)"
                fontSize={8}
                tickFormatter={(val) => `₹${val ? (val / 1000).toFixed(0) : '0'}k`}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0a0a0b', border: '1px solid var(--border)', fontSize: '10px' }}
                itemStyle={{ fontSize: '10px' }}
                labelStyle={{ fontWeight: 'bold', marginBottom: '4px' }}
              />
              <Area
                type="monotone"
                dataKey="value"
                name="QUAD Equity"
                stroke="var(--primary)"
                fillOpacity={1}
                fill="url(#colorValue)"
                strokeWidth={3}
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="benchmark_value"
                name="Benchmark (Buy&Hold)"
                stroke="var(--muted-foreground)"
                fill="transparent"
                strokeDasharray="5 5"
                strokeWidth={1}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Trade Record Strip */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Recent Performance Nodes</span>
            <span className="text-[9px] text-muted-foreground font-mono uppercase">Simulation ID: {simulationId}</span>
          </div>
          <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-none">
            {data.trades.slice(-10).map((trade: any, idx: number) => (
              <div
                key={idx}
                className={cn(
                  "min-w-[40px] h-10 rounded border flex flex-col items-center justify-center",
                  trade.pnl > 0 ? "bg-success/5 border-success/20" : "bg-destructive/5 border-destructive/20"
                )}
              >
                <span className={cn(
                  "text-[8px] font-black",
                  trade.pnl > 0 ? "text-success" : "text-destructive"
                )}>{trade.pnl_pct > 0 ? '+' : ''}{(trade.pnl_pct ?? 0).toFixed(1)}%</span>
                <span className="text-[7px] text-muted-foreground/60 font-mono uppercase">{trade.signal.slice(0, 1)}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
