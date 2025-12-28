'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Users, BarChart3, ChevronRight, Activity, Medal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import api from '@/lib/api/client';

interface PeerComparisonProps {
  symbol: string;
}

export default function PeerComparison({ symbol }: PeerComparisonProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPeers() {
      if (!symbol) return;
      try {
        setLoading(true);
        const response = await api.get(`/quad/${symbol}/peers`);
        setData(response.data);
      } catch (err) {
        console.error('Failed to load peer comparison', err);
      } finally {
        setLoading(false);
      }
    }
    fetchPeers();
  }, [symbol]);

  if (loading) {
    return (
      <Card className="bg-card border-border h-[300px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </Card>
    );
  }

  if (!data || data.total_peers <= 1) {
    return (
      <Card className="bg-card border-border h-[300px] flex flex-col items-center justify-center p-6 text-center">
         <div className="p-3 bg-muted/20 rounded-full border border-border mb-4">
           <Users className="w-8 h-8 text-muted-foreground" />
         </div>
         <h4 className="text-muted-foreground font-bold mb-1 uppercase tracking-wider text-sm">Sector Context Pending</h4>
         <p className="text-muted-foreground/60 text-[11px] max-w-xs mx-auto italic">
           Insufficient peer data for {symbol} in the {data?.sector || 'relevant'} sector.
         </p>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border overflow-hidden shadow-xl">
      <CardHeader className="py-2 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground font-black flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-primary" />
            Sector Performance
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-tighter">Rank</span>
            <span className="text-sm font-black text-primary">#{data.rank}/{data.total_peers}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="p-4 pb-2">
            <div className="flex items-center justify-between mb-2">
              <div className="space-y-0.5">
                <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Sector Avg</div>
                <div className="text-lg font-black tabular-nums">{data.avg_sector_conviction.toFixed(0)}%</div>
              </div>
              <div className="text-right space-y-0.5">
                <div className="text-[8px] text-muted-foreground uppercase font-black tracking-widest">Alpha</div>
                <div className={cn(
                  "text-lg font-black tabular-nums",
                  (data.peers.find((p:any) => p.is_self)?.conviction || 0) > data.avg_sector_conviction ? "text-success" : "text-destructive"
                )}>
                  {(data.peers.find((p:any) => p.is_self)?.conviction || 0) - data.avg_sector_conviction > 0 ? '+' : ''}
                  {((data.peers.find((p:any) => p.is_self)?.conviction || 0) - data.avg_sector_conviction).toFixed(0)}%
                </div>
              </div>
            </div>
        </div>

        {/* Peer List */}
        <div className="border-t border-border">
          {data.peers.map((peer: any, index: number) => (
            <div 
              key={peer.symbol} 
              className={cn(
                "flex items-center justify-between p-2 px-4 border-b border-border/50 hover:bg-muted/10 transition-colors",
                peer.is_self && "bg-primary/5 border-l-2 border-l-primary"
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-[8px] font-mono text-muted-foreground w-4">{index + 1}</span>
                <span className={cn(
                  "text-[10px] font-black tracking-tight",
                  peer.is_self ? "text-primary" : "text-foreground"
                )}>
                  {peer.symbol}
                </span>
                {peer.is_self && < Medal className="w-2.5 h-2.5 text-primary" />}
              </div>
              <div className="flex items-center gap-3">
                <div className={cn(
                  "text-[8px] px-1 py-0 rounded font-bold",
                  peer.signal === 'BUY' ? "bg-success/10 text-success" : 
                  peer.signal === 'SELL' ? "bg-destructive/10 text-destructive" :
                  "bg-muted text-muted-foreground"
                )}>
                  {peer.signal}
                </div>
                <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
                   <div 
                     className={cn(
                       "h-full",
                       peer.conviction >= 70 ? "bg-success" : peer.conviction >= 40 ? "bg-warning" : "bg-destructive"
                     )}
                     style={{ width: `${peer.conviction}%` }}
                   />
                </div>
                <span className="text-[10px] font-mono font-black tabular-nums w-6">{peer.conviction}%</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
