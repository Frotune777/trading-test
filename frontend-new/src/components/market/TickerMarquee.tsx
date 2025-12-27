'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface TickerItem {
  symbol: string;
  price: string;
  change: string;
  changePercent: string;
  isPositive: boolean;
}

const MOCK_TICKERS: TickerItem[] = [
  { symbol: 'NIFTY 50', price: '26,042.30', change: '-98.45', changePercent: '0.38%', isPositive: false },
  { symbol: 'NIFTY BANK', price: '59,011.35', change: '-124.20', changePercent: '0.21%', isPositive: false },
  { symbol: 'SENSEX', price: '85,041.45', change: '-342.10', changePercent: '0.40%', isPositive: false },
  { symbol: 'BAJFINANCE', price: '7,432.00', change: '+85.50', changePercent: '1.16%', isPositive: true },
  { symbol: 'HDFCBANK', price: '1,642.10', change: '-15.30', changePercent: '0.92%', isPositive: false },
  { symbol: 'RELIANCE', price: '2,890.00', change: '+12.45', changePercent: '0.43%', isPositive: true },
  { symbol: 'TCS', price: '4,120.00', change: '-28.40', changePercent: '0.68%', isPositive: false },
];

export function TickerMarquee() {
  return (
    <div className="w-full bg-black py-2 overflow-hidden border-b border-white/10 select-none">
      <div className="flex whitespace-nowrap animate-[marquee_40s_linear_infinite] hover:[animation-play-state:paused]">
        {/* First set of items */}
        <div className="flex items-center gap-8 px-4">
          {MOCK_TICKERS.map((item, idx) => (
            <div key={`${item.symbol}-${idx}`} className="flex items-center gap-2 group cursor-pointer">
              <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest group-hover:text-white transition-colors">
                {item.symbol}
              </span>
              <span className="text-xs font-mono font-medium text-white">
                {item.price}
              </span>
              <span className={cn(
                "text-[10px] font-bold flex items-center gap-0.5",
                item.isPositive ? "text-success" : "text-destructive"
              )}>
                {item.isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {item.changePercent}
              </span>
            </div>
          ))}
        </div>
        {/* Duplicate set for seamless loop */}
        <div className="flex items-center gap-8 px-4">
          {MOCK_TICKERS.map((item, idx) => (
            <div key={`${item.symbol}-dupe-${idx}`} className="flex items-center gap-2 group cursor-pointer">
              <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest group-hover:text-white transition-colors">
                {item.symbol}
              </span>
              <span className="text-xs font-mono font-medium text-white">
                {item.price}
              </span>
              <span className={cn(
                "text-[10px] font-bold flex items-center gap-0.5",
                item.isPositive ? "text-success" : "text-destructive"
              )}>
                {item.isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {item.changePercent}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
