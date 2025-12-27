'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { MarketMood } from '@/lib/api/market-api';

interface MarketMoodGaugeProps {
  data: MarketMood;
  isLoading?: boolean;
}

export function MarketMoodGauge({ data, isLoading }: MarketMoodGaugeProps) {
  // Map score to needle rotation (0 to 180 degrees)
  const rotation = (data.score / 100) * 180 - 90;

  const getColor = (score: number) => {
    if (score >= 80) return 'text-orange-600'; // Extreme Greed
    if (score >= 65) return 'text-orange-500'; // Greed
    if (score <= 20) return 'text-success'; // Extreme Fear (buying opportunity)
    if (score <= 35) return 'text-success/80'; // Fear
    return 'text-warning'; // Neutral
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 flex flex-col items-center justify-center relative overflow-hidden h-full">
      <div className="flex items-center justify-between w-full mb-8">
        <div>
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Market Mood Index</h4>
          <p className="text-[10px] text-muted-foreground/60 italic">Change since yesterday</p>
        </div>
        <div className="text-right">
          <span className={cn("text-lg font-bold", getColor(data.score))}>
            {data.current_val}
          </span>
          <p className="text-[10px] text-muted-foreground/60">to {data.previous_val}</p>
        </div>
      </div>

      {/* Gauge Illustration */}
      <div className="relative w-64 h-32 mt-4">
        {/* Semi-circle track */}
        <div className="absolute inset-0 rounded-t-full border-[10px] border-muted overflow-hidden">
          <div className="flex h-full w-full">
            <div className="h-full w-[20%] bg-success" title="Extreme Fear" />
            <div className="h-full w-[15%] bg-success/60" title="Fear" />
            <div className="h-full w-[30%] bg-warning" title="Neutral" />
            <div className="h-full w-[15%] bg-orange-400" title="Greed" />
            <div className="h-full w-[20%] bg-orange-600" title="Extreme Greed" />
          </div>
        </div>

        {/* Needle */}
        <div 
          className="absolute bottom-0 left-1/2 w-1.5 h-24 bg-foreground origin-bottom rounded-full transition-transform duration-1000 ease-out z-10"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
        >
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-foreground rounded-full" />
        </div>
        
        {/* Center hub */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-8 h-8 bg-card border-4 border-foreground rounded-full z-20" />
      </div>

      {/* Score Text */}
      <div className="mt-4 flex items-center gap-2">
         <span className="text-3xl font-black text-foreground">{data.score}</span>
         <div className="h-6 w-px bg-border mx-1" />
         <span className="text-xs font-bold text-muted-foreground uppercase tracking-tighter">Sentiment<br/>Aggregate</span>
      </div>

      <div className="grid grid-cols-5 w-full mt-8 border-t border-border pt-4 text-[9px] font-bold text-muted-foreground uppercase tracking-tighter text-center">
        <div>Extreme Fear</div>
        <div>Fear</div>
        <div>Neutral</div>
        <div>Greed</div>
        <div>Extreme Greed</div>
      </div>

      {isLoading && (
        <div className="absolute inset-0 bg-card/60 backdrop-blur-[1px] flex items-center justify-center">
          <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      )}
    </div>
  );
}
