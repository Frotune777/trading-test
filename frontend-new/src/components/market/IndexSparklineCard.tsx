'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { MarketIndex } from '@/lib/api/market-api';

interface IndexSparklineCardProps {
  index: MarketIndex;
  isLoading?: boolean;
}

export function IndexSparklineCard({ index, isLoading }: IndexSparklineCardProps) {
  // Generate a mock sparkline path if history isn't provided
  const generatePath = () => {
    const points = index.history || [40, 45, 38, 52, 48, 60, 55, 65, 62, 70];
    const width = 100;
    const height = 30;
    const step = width / (points.length - 1);
    const max = Math.max(...points);
    const min = Math.min(...points);
    const range = max - min || 1;

    return points.map((p, i) => {
      const x = i * step;
      const y = height - ((p - min) / range) * height;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  };

  return (
    <div className="bg-card border border-border rounded-xl p-4 hover:border-primary/40 transition-all group flex items-start justify-between">
      <div className="space-y-1">
        <h4 className="text-xs font-bold text-muted-foreground uppercase opacity-60 tracking-wider">
          {index.name}
        </h4>
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-black text-foreground tabular-nums">
            {index.value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className={cn(
          "flex items-center gap-1 text-[11px] font-bold",
          index.is_up ? "text-success" : "text-destructive"
        )}>
          {index.is_up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          <span>{index.change > 0 ? '+' : ''}{(index.change_percent ?? 0).toFixed(2)}%</span>
        </div>
      </div>

      <div className="h-10 w-24 self-center mt-2">
        <svg width="100%" height="100%" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path
            d={generatePath()}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={cn(index.is_up ? "text-success" : "text-destructive")}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {isLoading && (
        <div className="absolute inset-0 bg-card/60 backdrop-blur-[1px] rounded-xl flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      )}
    </div>
  );
}
