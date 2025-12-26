'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Minus, 
  HelpCircle,
  Activity,
  Zap,
  Shield,
  BarChart3,
  Waves,
  Cpu
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface PillarData {
  name: string;
  score: number;
  bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  is_placeholder: boolean;
  weight: number;
  summary: string;
}

interface PillarContributionProps {
  pillars: Record<string, any>;
}

const PILLAR_ICONS: Record<string, React.ReactNode> = {
  trend: <Activity className="w-4 h-4" />,
  momentum: <Zap className="w-4 h-4" />,
  volatility: <Waves className="w-4 h-4" />,
  liquidity: <BarChart3 className="w-4 h-4" />,
  sentiment: <Cpu className="w-4 h-4" />,
  regime: <Shield className="w-4 h-4" />
};

export default function PillarContribution({ pillars }: PillarContributionProps) {
  const pillarList = Object.entries(pillars).map(([id, data]) => ({
    id,
    name: id.charAt(0).toUpperCase() + id.slice(1),
    ...data
  }));

  const getBiasConfig = (bias: string) => {
    switch (bias) {
      case 'BULLISH':
        return { 
          color: 'text-emerald-500', 
          bg: 'bg-emerald-500/10', 
          border: 'border-emerald-500/20',
          indicator: <ArrowUpRight className="w-4 h-4" />
        };
      case 'BEARISH':
        return { 
          color: 'text-rose-500', 
          bg: 'bg-rose-500/10', 
          border: 'border-rose-500/20',
          indicator: <ArrowDownRight className="w-4 h-4" />
        };
      default:
        return { 
          color: 'text-amber-500', 
          bg: 'bg-amber-500/10', 
          border: 'border-amber-500/20',
          indicator: <Minus className="w-4 h-4" />
        };
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-[0.2em] font-black text-slate-500">Pillar Contribution Breakdown</h3>
        <span className="text-[10px] text-slate-600 font-mono">WEIGHT-ADJUSTED CALCULATION</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {pillarList.map((pillar) => {
          const config = getBiasConfig(pillar.bias);
          return (
            <Card key={pillar.id} className={cn(
              "bg-slate-900 border-slate-800 relative overflow-hidden group hover:border-slate-700 transition-colors",
              pillar.is_placeholder && "opacity-60"
            )}>
              {/* Highlight bar */}
              <div className={cn("absolute top-0 left-0 bottom-0 w-1", 
                pillar.bias === 'BULLISH' ? 'bg-emerald-500' : 
                pillar.bias === 'BEARISH' ? 'bg-rose-500' : 'bg-amber-500'
              )} />
              
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-slate-950 rounded border border-slate-800 text-slate-400 group-hover:text-slate-200">
                      {PILLAR_ICONS[pillar.id] || <HelpCircle className="w-4 h-4" />}
                    </div>
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">{pillar.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {pillar.is_placeholder && (
                      <span className="text-[9px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded font-bold uppercase">PLACEHOLDER</span>
                    )}
                    <span className="text-[10px] text-slate-500 font-mono">{(pillar.weight * 100).toFixed(0)}% WT</span>
                  </div>
                </div>

                <div className="flex items-end justify-between mb-3">
                  <div className="text-3xl font-mono font-black text-white leading-none">
                    {pillar.score.toFixed(0)}
                  </div>
                  <div className={cn(
                    "flex items-center gap-1 font-bold text-xs px-2 py-1 rounded",
                    config.bg, config.color, config.border
                  )}>
                    {config.indicator} {pillar.bias}
                  </div>
                </div>

                {/* Explanation Text */}
                <div className="text-[11px] leading-relaxed text-slate-400 line-clamp-2 h-8 italic border-t border-slate-800/50 pt-2 group-hover:text-slate-300 transition-colors overflow-hidden">
                  {pillar.reasoning || pillar.metrics?.summary || (pillar.is_placeholder ? "Tracking not yet initialized. Returning neutral baseline." : "Metric within expected parameters.")}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
