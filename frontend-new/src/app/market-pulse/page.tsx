'use client';

import React, { useEffect, useState } from 'react';
import { marketAPI, MarketIndex, MarketMood, MarketBreadth } from '@/lib/api/market-api';
import { TickerMarquee } from '@/components/market/TickerMarquee';
import { MarketMoodGauge } from '@/components/market/MarketMoodGauge';
import { IndexSparklineCard } from '@/components/market/IndexSparklineCard';
import { ChevronRight, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MarketBreadthWidget } from '@/components/dashboard/market-breadth-widget';

export default function MarketPulsePage() {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [mood, setMood] = useState<MarketMood | null>(null);
  const [breadth, setBreadth] = useState<MarketBreadth | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState<string>("NIFTY 50");

  useEffect(() => {
    async function fetchData() {
      try {
        const [indicesRes, moodRes, breadthRes] = await Promise.all([
          marketAPI.getIndices(),
          marketAPI.getMarketMood(),
          marketAPI.getMarketBreadth()
        ]);
        setIndices(indicesRes?.data || []);
        setMood(moodRes);
        setBreadth(breadthRes);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Sidebar would be handled by a higher level layout, but for standalone test: */}
      <div className="flex-1 flex flex-col">
        {/* Top Ticker - Always Dark */}
        <TickerMarquee />

        {/* Dashboard Top Section - Dark Theme Replicated */}
        <div className="bg-[#121417] text-white p-8 border-b border-white/5 shadow-2xl relative overflow-hidden">
          {/* Subtle background glow */}
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2" />
          
          <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-3 gap-8 relative z-10">
            {/* Left: Main Indices Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(indices || []).slice(0, 2).map((idx) => (
                <div key={idx.name} className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-colors cursor-pointer">
                  <div className="text-[11px] font-black text-white/40 uppercase tracking-[0.2em] mb-4">{idx.name}</div>
                  <div className="text-3xl font-black mb-1">{idx.value?.toLocaleString()}</div>
                  <div className={cn(
                    "text-sm font-bold flex items-center gap-1",
                    idx.is_up ? "text-success" : "text-destructive"
                  )}>
                    {idx.is_up ? '▲' : '▼'} {(idx.change_percent ?? 0).toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>

            {/* Center: Market Mood Index */}
            <div className="xl:px-8">
               {mood && <MarketMoodGauge data={mood} isLoading={loading} />}
            </div>

            {/* Right: MMI History (Replicating the balls in the image) */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[11px] font-black text-white/40 uppercase tracking-widest">Sentiment Trend</span>
                <ChevronRight className="w-4 h-4 text-white/20" />
              </div>
              
              <div className="flex items-center justify-around mt-4">
                {['FRI', 'MON', 'TUE', 'WED', 'FRI'].map((day, i) => (
                   <div key={`${day}-${i}`} className="flex flex-col items-center gap-2">
                      <div className={cn(
                        "w-10 h-10 rounded-full border-2 border-white/10 flex items-center justify-center relative",
                        i === 4 ? "bg-orange-500 border-none ring-4 ring-orange-500/20 shadow-lg shadow-orange-500/40" : "bg-white/5"
                      )}>
                         <div className={cn(
                           "w-2 h-2 rounded-full",
                           i < 2 ? "bg-success" : i < 4 ? "bg-warning" : "bg-white"
                         )} />
                      </div>
                      <span className="text-[10px] font-bold text-white/40">{day}</span>
                   </div>
                ))}
              </div>
              
              <p className="text-[10px] text-white/30 text-center mt-6 uppercase tracking-tighter">
                Institutional Sentiment is currently <span className="text-orange-400 font-bold">GREED</span>
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Content Area - Clean Institutional Light/High-Contrast Theme */}
        <main className="flex-1 p-8 bg-[#f8fafc] dark:bg-[#0a0c0f]">
          <div className="max-w-[1600px] mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-black text-foreground tracking-tight">Market and sectors</h2>
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Focus Index:</span>
                <Select value={selectedIndex} onValueChange={setSelectedIndex}>
                  <SelectTrigger className="w-[180px] bg-card border-border font-bold">
                    <SelectValue placeholder="Select Index" />
                  </SelectTrigger>
                  <SelectContent>
                    {indices.length > 0 ? (
                      indices.map((idx) => (
                        <SelectItem key={idx.name} value={idx.name}>
                          {idx.name}
                        </SelectItem>
                      ))
                    ) : (
                      <>
                        <SelectItem value="NIFTY 50">NIFTY 50</SelectItem>
                        <SelectItem value="NIFTY BANK">NIFTY BANK</SelectItem>
                        <SelectItem value="NIFTY IT">NIFTY IT</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 font-geist-sans">
               {(indices || []).map((idx) => (
                 <IndexSparklineCard key={idx.name} index={idx} isLoading={loading} />
               ))}
               
               {/* Market Breadth Integration */}
               <div className="col-span-1 md:col-span-2">
                 <MarketBreadthWidget index={selectedIndex} />
               </div>
            </div>

            {/* Sector Section Replicated */}
            <div className="mt-16 grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-card border border-border rounded-2xl p-8 shadow-sm">
                <h3 className="text-lg font-black mb-6 flex items-center gap-2 italic">
                   <div className="w-1.5 h-6 bg-primary rounded-full" />
                   Sector Rotation (24h)
                </h3>
                <div className="space-y-4">
                  {[
                    { name: 'NIFTY IT', val: '+2.45%', up: true },
                    { name: 'NIFTY AUTO', val: '+1.12%', up: true },
                    { name: 'NIFTY PHARMA', val: '-0.34%', up: false },
                    { name: 'NIFTY PSU BANK', val: '-1.20%', up: false },
                  ].map(s => (
                    <div key={s.name} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted transition-colors border border-transparent hover:border-border">
                      <span className="text-sm font-bold text-foreground">{s.name}</span>
                      <span className={cn(
                        "text-xs font-black px-2 py-1 rounded",
                        s.up ? "text-success bg-success/10" : "text-destructive bg-destructive/10"
                      )}>{s.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gradient-to-br from-primary to-accent rounded-2xl p-8 text-white relative overflow-hidden group">
                 <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000" />
                 <h3 className="text-2xl font-black mb-2 relative z-10">Advanced Analytics v2.0</h3>
                 <p className="text-white/80 text-sm mb-6 max-w-xs relative z-10">Get deep-dive sentiment analysis and institutional flow-tracking on 500+ stocks.</p>
                 <button className="bg-white text-primary font-black px-6 py-3 rounded-xl hover:bg-black hover:text-white transition-all shadow-xl relative z-10">
                   Check diversification score
                 </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
