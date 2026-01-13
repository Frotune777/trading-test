'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceArea,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { marketAPI } from '@/lib/api/market-api';
import { Loader2, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VolumeProfileProps {
  symbol: string;
}

export default function VolumeProfile({ symbol }: VolumeProfileProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchVolumeProfile() {
      if (!symbol) return;
      try {
        setLoading(true);
        const response = await marketAPI.getVolumeProfile(symbol, 30, 40);
        setData(response);
      } catch (err) {
        console.error('Failed to load volume profile', err);
      } finally {
        setLoading(false);
      }
    }
    fetchVolumeProfile();
  }, [symbol]);

  if (loading) {
    return (
      <Card className="bg-card border-border h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </Card>
    );
  }

  if (!data || !data.profile || data.profile.length === 0) {
    return (
      <Card className="bg-card border-border h-[400px] flex items-center justify-center">
        <p className="text-muted-foreground text-xs uppercase font-black tracking-widest">No Profile Data Available</p>
      </Card>
    );
  }

  // Value Area Highlights
  const isValueArea = (price: number) => price >= data.val && price <= data.vah;

  return (
    <Card className="bg-card border-border overflow-hidden shadow-2xl">
      <CardHeader className="py-2 px-3 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[9px] uppercase tracking-[0.2em] text-muted-foreground font-black flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-warning" />
            Institutional Volume Profile
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="flex flex-col items-end">
              <span className="text-[7px] text-muted-foreground font-black uppercase">POC</span>
              <span className="text-[9px] font-mono font-bold text-primary">₹{data.poc?.toFixed(2) || '--'}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0 h-[280px] relative min-w-0 min-h-[280px]">
        {/* Value Area Range Indicator */}
        <div className="absolute left-2 top-2 bottom-2 w-1 border-r border-dashed border-primary/30 z-10 flex flex-col justify-between">
          <span className="text-[7px] text-primary font-black -rotate-90 origin-left ml-2 whitespace-nowrap">VAH: ₹{data.vah?.toFixed(0) || '--'}</span>
          <span className="text-[7px] text-primary font-black -rotate-90 origin-left ml-2 whitespace-nowrap">VAL: ₹{data.val?.toFixed(0) || '--'}</span>
        </div>

        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data.profile}
            layout="vertical"
            margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
          >
            <XAxis type="number" hide />
            <YAxis
              dataKey="price"
              type="number"
              domain={['auto', 'auto']}
              orientation="right"
              tick={{ fontSize: 8, fill: '#71717a' }}
              tickFormatter={(val) => `₹${val?.toFixed?.(0) ?? val ?? '--'}`}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="bg-[#0a0a0b] border border-white/10 p-2 rounded shadow-2xl space-y-1">
                      <div className="text-[10px] text-muted-foreground font-black uppercase tracking-widest border-b border-white/5 pb-1 mb-1">
                        Price: ₹{item.price?.toFixed(2) || '--'}
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-[9px] text-success font-bold uppercase">Buy Vol</span>
                        <span className="text-[9px] font-mono">{item.buy_volume ? (item.buy_volume / 1000).toFixed(1) : '0'}K</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-[9px] text-destructive font-bold uppercase">Sell Vol</span>
                        <span className="text-[9px] font-mono">{item.sell_volume ? (item.sell_volume / 1000).toFixed(1) : '0'}K</span>
                      </div>
                      <div className="flex justify-between gap-4 pt-1 border-t border-white/5">
                        <span className="text-[9px] text-foreground font-black uppercase">Total</span>
                        <span className="text-[9px] font-mono font-bold">{item.volume ? (item.volume / 1000).toFixed(1) : '0'}K</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Value Area Highlight */}
            <ReferenceLine y={data.poc} stroke="#2563eb" strokeWidth={2} strokeDasharray="3 3" />

            <Bar dataKey="buy_volume" stackId="a" isAnimationActive={false}>
              {data.profile.map((entry: any, index: number) => (
                <Cell
                  key={`cell-buy-${index}`}
                  fill={isValueArea(entry.price) ? '#10b981' : '#10b981'}
                  opacity={isValueArea(entry.price) ? 0.6 : 0.2}
                />
              ))}
            </Bar>
            <Bar dataKey="sell_volume" stackId="a" isAnimationActive={false}>
              {data.profile.map((entry: any, index: number) => (
                <Cell
                  key={`cell-sell-${index}`}
                  fill={isValueArea(entry.price) ? '#f43f5e' : '#f43f5e'}
                  opacity={isValueArea(entry.price) ? 0.6 : 0.2}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
      <div className="bg-muted/30 border-t border-border p-3 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="text-[8px] text-muted-foreground font-black uppercase tracking-widest">Live Node Distribution</span>
        </div>
        <div className="flex items-center gap-4 text-[8px] font-black uppercase tracking-tighter">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-primary rounded-sm" />
            <span className="text-muted-foreground">Value Area (70%)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-muted rounded-sm" />
            <span className="text-muted-foreground">Outside VA</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
