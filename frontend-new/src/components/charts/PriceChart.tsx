'use client';

import React, { useEffect, useState } from 'react';
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Line
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { marketAPI } from '@/lib/api/market-api';
import { Loader2, TrendingUp, TrendingDown, Maximize2 } from 'lucide-react';

interface PriceChartProps {
  symbol: string;
  days?: number;
}

export default function PriceChart({ symbol, days = 30 }: PriceChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchChart() {
      if (!symbol) return;
      try {
        setLoading(true);
        const response = await marketAPI.getHistory(symbol, days);

        // Transform for candlestick
        // Recharts doesn't have a native candlestick, so we use Bar for body and another Bar for wick
        const transformed = response.data.map(item => ({
          ...item,
          // For Bar chart implementation:
          // openClose: [open, close]
          // highLow: [low, high]
          isUp: item.close >= item.open,
          body: [Math.min(item.open, item.close), Math.max(item.open, item.close)],
          wick: [item.low, item.high],
          mid: (item.open + item.close) / 2
        }));

        setData(transformed);
      } catch (err: any) {
        setError(err.message || 'Failed to load price history');
      } finally {
        setLoading(false);
      }
    }
    fetchChart();
  }, [symbol, days]);

  if (loading) {
    return (
      <Card className="bg-card border-border h-[400px] min-h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <span className="ml-2 text-xs text-muted-foreground animate-pulse">Loading Price Data...</span>
      </Card>
    );
  }

  if (error || data.length === 0) {
    return (
      <Card className="bg-card border-border h-[400px] flex items-center justify-center p-6 text-center">
        <div className="text-muted-foreground text-sm">
          Historical price chart data unavailable for {symbol}.
        </div>
      </Card>
    );
  }

  const latestPrice = data[data.length - 1]?.close || 0;
  const prevPrice = data[data.length - 2]?.close || 0;
  const change = latestPrice - prevPrice;
  const changePercent = prevPrice > 0 ? (change / prevPrice) * 100 : 0;

  return (
    <Card className="bg-card border-border overflow-hidden min-h-[350px] shadow-lg">
      <CardHeader className="py-2 px-4 border-b border-border flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground font-black">Price Action History</CardTitle>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-base font-mono font-black tabular-nums">₹{latestPrice.toLocaleString()}</span>
              <span className={`text-[9px] font-bold px-1 py-0.5 rounded flex items-center gap-0.5 ${change >= 0 ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'}`}>
                {change >= 0 ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                {isFinite(changePercent) ? changePercent.toFixed(2) : '0.00'}%
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[9px] text-muted-foreground font-mono uppercase tracking-tighter bg-muted/30 px-1.5 py-0.5 rounded">OHLCV / {days}D</span>
          <button className="text-muted-foreground hover:text-foreground">
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="p-0 pt-4 pr-2 pb-2">
        <div className="h-[250px] w-full min-w-0 min-h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="time"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                minTickGap={30}
              />
              <YAxis
                domain={['auto', 'auto']}
                orientation="right"
                axisLine={false}
                tickLine={false}
                tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0a0a0b',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace'
                }}
                itemStyle={{ color: '#fff' }}
              />

              {/* Wick using Bar */}
              <Bar dataKey="wick" stroke="none" fill="rgba(255,255,255,0.3)">
                {data.map((entry, index) => (
                  <Cell key={`wick-${index}`} fill={entry.isUp ? '#10b981' : '#f43f5e'} opacity={0.3} />
                ))}
              </Bar>

              {/* Body using Bar */}
              <Bar dataKey="body" stroke="none">
                {data.map((entry, index) => (
                  <Cell key={`body-${index}`} fill={entry.isUp ? '#10b981' : '#f43f5e'} />
                ))}
              </Bar>

              {/* SMA-20 Line approximation if we want, or just the trend */}
              <Line type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} dot={false} opacity={0.5} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
