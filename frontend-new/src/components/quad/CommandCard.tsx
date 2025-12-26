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
          color: 'text-emerald-500', 
          bg: 'bg-emerald-500/10', 
          border: 'border-emerald-500/20',
          icon: <TrendingUp className="w-8 h-8" />
        };
      case 'SELL':
        return { 
          color: 'text-rose-500', 
          bg: 'bg-rose-500/10', 
          border: 'border-rose-500/20',
          icon: <TrendingDown className="w-8 h-8" />
        };
      case 'HOLD':
        return { 
          color: 'text-amber-500', 
          bg: 'bg-amber-500/10', 
          border: 'border-amber-500/20',
          icon: <Minus className="w-8 h-8" />
        };
      default:
        return { 
          color: 'text-slate-400', 
          bg: 'bg-slate-400/10', 
          border: 'border-slate-400/20',
          icon: <AlertCircle className="w-8 h-8" />
        };
    }
  };

  const config = getSignalConfig(signal);
  const formattedTime = format(new Date(timestamp), 'HH:mm:ss');
  const formattedDate = format(new Date(timestamp), 'MMM dd, yyyy');

  return (
    <Card className="bg-slate-900 border-slate-800 text-slate-100 overflow-hidden shadow-2xl">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 lg:grid-cols-12">
          {/* Signal Section */}
          <div className={cn(
            "lg:col-span-5 p-8 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-800",
            config.bg
          )}>
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className="border-slate-700 bg-slate-900/50 text-slate-400 font-mono tracking-tighter">
                  {symbol}
                </Badge>
                {isExecutionReady && (
                  <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white gap-1 flex items-center">
                    <ShieldCheck className="w-3 h-3" /> READY
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                <Clock className="w-3 h-3" /> {formattedTime} IST
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className={cn("p-4 rounded-xl border", config.border, "bg-slate-950")}>
                {config.icon}
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-1 font-bold">QUAD Signal</div>
                <div className={cn("text-5xl font-black tracking-tighter", config.color)}>
                  {signal}
                </div>
              </div>
            </div>

            <div className="mt-12 grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-lg">
                <div className="text-[10px] uppercase text-slate-500 mb-1 font-bold">Confidence</div>
                <div className={cn(
                  "text-sm font-bold",
                  confidence === 'HIGH' ? 'text-emerald-400' : 
                  confidence === 'MEDIUM' ? 'text-amber-400' : 'text-rose-400'
                )}>
                  {confidence}
                </div>
              </div>
              <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-lg">
                <div className="text-[10px] uppercase text-slate-500 mb-1 font-bold">Regime</div>
                <div className="text-sm font-bold text-slate-200 uppercase">{regime}</div>
              </div>
            </div>
          </div>

          {/* Conviction Section */}
          <div className="lg:col-span-7 p-8 bg-slate-900/40">
            <div className="flex flex-col h-full justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="text-xs uppercase tracking-widest text-slate-500 font-bold flex items-center gap-2">
                    <Zap className="w-3 h-3 text-amber-500" /> Analysis Conviction
                  </div>
                  <div className="text-4xl font-mono text-white font-black leading-none">
                    {conviction.toFixed(1)}%
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden mb-8 border border-slate-700/50">
                  <div 
                    className={cn(
                      "h-full transition-all duration-1000 ease-out",
                      conviction >= 70 ? "bg-emerald-500" : 
                      conviction >= 50 ? "bg-amber-500" : "bg-rose-500"
                    )}
                    style={{ width: `${conviction}%` }}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="text-[10px] uppercase text-slate-500 mb-2 font-bold tracking-wider">Data window</div>
                    <div className="text-sm text-slate-300 bg-slate-800/50 p-2 rounded border border-slate-700 font-mono">
                      {dataWindow}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-slate-500 mb-2 font-bold tracking-wider">Last Sync</div>
                    <div className="text-sm text-slate-300 bg-slate-800/50 p-2 rounded border border-slate-700 font-mono">
                      {formattedDate}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-8 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
                <p>INSTITUTIONAL CALIBRATION V1.1.0 (MATRIX_2024_Q4)</p>
                <p className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> ENGINE ONLINE
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
