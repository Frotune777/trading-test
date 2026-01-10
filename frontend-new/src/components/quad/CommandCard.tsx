'use client';

import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  Clock,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface CommandCardProps {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD' | 'INVALID';
  conviction: number;
  confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  regime: string;
  timestamp: string;
  dataWindow: string;
  isExecutionReady: boolean;
}

export default function CommandCard({
  symbol,
  signal,
  conviction,
  confidence,
  regime,
  timestamp,
  dataWindow,
  isExecutionReady
}: CommandCardProps) {
  const getSignalConfig = (s: string) => {
    switch (s) {
      case 'BUY':
        return {
          color: 'text-success',
          bg: 'bg-success/10',
          border: 'border-success/20',
          icon: <TrendingUp className="w-8 h-8" />
        };
      case 'SELL':
        return {
          color: 'text-destructive',
          bg: 'bg-destructive/10',
          border: 'border-destructive/20',
          icon: <TrendingDown className="w-8 h-8" />
        };
      case 'HOLD':
        return {
          color: 'text-warning',
          bg: 'bg-warning/10',
          border: 'border-warning/20',
          icon: <Minus className="w-8 h-8" />
        };
      default:
        return {
          color: 'text-muted-foreground',
          bg: 'bg-muted/10',
          border: 'border-border',
          icon: <AlertCircle className="w-8 h-8" />
        };
    }
  };

  const config = getSignalConfig(signal);
  const formattedTime = format(new Date(timestamp), 'HH:mm:ss');
  const formattedDate = format(new Date(timestamp), 'MMM dd, yyyy');

  return (
    <Card className="bg-card border-border text-foreground overflow-hidden shadow-2xl">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 lg:grid-cols-12">
          {/* Signal Section */}
          <div className={cn(
            "lg:col-span-5 p-8 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-border",
            config.bg
          )}>
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="border-border bg-background/50 text-muted-foreground font-mono tracking-tighter">
                  {symbol}
                </Badge>
                {isExecutionReady && (
                  <Badge className="bg-success hover:bg-success/90 text-white gap-1 flex items-center border-none" data-testid="execution-ready-badge">
                    <ShieldCheck className="w-3 h-3" /> READY
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
                <Clock className="w-3 h-3" /> {formattedTime} IST
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className={cn("p-4 rounded-xl border", config.border, "bg-background/80")}>
                {config.icon}
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-1 font-bold">QUAD Signal</div>
                <div className={cn("text-5xl font-black tracking-tighter", config.color)} data-testid="quad-signal">
                  {signal}
                </div>
              </div>
            </div>

            <div className="mt-12 grid grid-cols-2 gap-4">
              <div className="p-3 bg-muted/20 border border-border rounded-lg">
                <div className="text-[10px] uppercase text-muted-foreground mb-1 font-bold">Confidence</div>
                <div className={cn(
                  "text-sm font-bold",
                  confidence === 'HIGH' ? 'text-success' :
                    confidence === 'MEDIUM' ? 'text-warning' : 'text-destructive'
                )}>
                  {confidence}
                </div>
              </div>
              <div className="p-3 bg-muted/20 border border-border rounded-lg">
                <div className="text-[10px] uppercase text-muted-foreground mb-1 font-bold">Regime</div>
                <div className="text-sm font-bold text-foreground uppercase">{regime}</div>
              </div>
            </div>
          </div>

          {/* Conviction Section */}
          <div className="lg:col-span-7 p-8 bg-muted/50">
            <div className="flex flex-col h-full justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="text-xs uppercase tracking-widest text-muted-foreground font-bold flex items-center gap-2">
                    <Zap className="w-3 h-3 text-amber-500" /> Analysis Conviction
                  </div>
                  <div className="text-4xl font-mono text-foreground font-black leading-none" data-testid="conviction-score">
                    {conviction.toFixed(1)}%
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-3 w-full bg-muted rounded-full overflow-hidden mb-8 border border-border">
                  <div
                    className={cn(
                      "h-full transition-all duration-1000 ease-out",
                      conviction >= 70 ? "bg-success" :
                        conviction >= 50 ? "bg-warning" : "bg-destructive"
                    )}
                    style={{ width: `${conviction}%` }}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground mb-2 font-bold tracking-wider">Data window</div>
                    <div className="text-sm text-foreground bg-muted/50 p-2 rounded border border-border font-mono">
                      {dataWindow}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground mb-2 font-bold tracking-wider">Last Sync</div>
                    <div className="text-sm text-foreground bg-muted/50 p-2 rounded border border-border font-mono">
                      {formattedDate}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-8 border-t border-border flex items-center justify-between text-[10px] text-muted-foreground">
                <p>INSTITUTIONAL CALIBRATION V1.1.0 (MATRIX_2024_Q4)</p>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> ENGINE ONLINE
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
