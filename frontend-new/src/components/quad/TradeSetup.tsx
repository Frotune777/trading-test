'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import {
  Target,
  ShieldCheck,
  ArrowUpCircle,
  ArrowDownCircle,
  Crosshair,
  TrendingDown,
  TrendingUp,
  Scale,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { tradeSignalsAPI, TradeSetup as TradeSetupData } from '@/lib/api/trade-signals-api';

interface TradeSetupProps {
  symbol: string;
}

export default function TradeSetup({ symbol }: TradeSetupProps) {
  const [setup, setSetup] = useState<TradeSetupData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSetup() {
      try {
        setLoading(true);
        const data = await tradeSignalsAPI.getTradeSetup(symbol);
        setSetup(data);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching trade setup:', err);
        setError(err.message || 'Failed to generate trade setup');
      } finally {
        setLoading(false);
      }
    }

    if (symbol) {
      fetchSetup();
    }
  }, [symbol]);

  if (loading) {
    return (
      <Card className="bg-card border-border border-dashed h-[300px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Calculating Zones...</span>
        </div>
      </Card>
    );
  }

  if (error || !setup) {
    return (
      <Card className="bg-destructive/5 border-destructive/20 p-6 flex flex-col items-center justify-center text-center">
        <AlertCircle className="w-8 h-8 text-destructive mb-2" />
        <h4 className="text-sm font-bold text-destructive uppercase tracking-wider">Setup Calculation Error</h4>
        <p className="text-xs text-muted-foreground mt-1">{error}</p>
      </Card>
    );
  }

  const { current_price, parameters, zones } = setup;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-[0.2em] font-black text-muted-foreground">Actionable Trade Setup</h3>
        <span className="text-[10px] text-muted-foreground font-mono bg-muted/30 px-2 py-0.5 rounded">VOLATILITY-ADAPTED LEVELS</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* SL/TP Targets */}
        <div className="xl:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* STOP LOSS */}
          <Card className="bg-destructive/5 border-destructive/20 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <TrendingDown className="w-12 h-12 text-destructive" />
            </div>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2 text-destructive">
                <ShieldCheck className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-wider">Rigid Stop-Loss</span>
              </div>
              <div className="text-3xl font-mono font-black text-foreground mb-1 tabular-nums" data-testid="trade-setup-sl">
                {parameters.stop_loss.toLocaleString()}
              </div>
              <div className="flex items-center justify-between text-[10px] text-muted-foreground font-bold font-mono">
                <span>RISK: {(((current_price - parameters.stop_loss) / current_price) * 100).toFixed(2)}%</span>
                <span className="text-destructive/60 uppercase">EXIT TRIGGER</span>
              </div>
            </CardContent>
          </Card>

          {/* TAKE PROFIT 1 */}
          <Card className="bg-success/5 border-success/20 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Target className="w-12 h-12 text-success" />
            </div>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2 text-success">
                <TrendingUp className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-wider">Target 1 (Base)</span>
              </div>
              <div className="text-3xl font-mono font-black text-foreground mb-1 tabular-nums" data-testid="trade-setup-tp1">
                {parameters.take_profit_1.toLocaleString()}
              </div>
              <div className="flex items-center justify-between text-[10px] text-muted-foreground font-bold font-mono">
                <span>REWARD: {(((parameters.take_profit_1 - current_price) / current_price) * 100).toFixed(2)}%</span>
                <span className="text-success/60 uppercase">RR 1.5x</span>
              </div>
            </CardContent>
          </Card>

          {/* TAKE PROFIT 2 */}
          <Card className="bg-blue-500/5 border-blue-500/20 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <ArrowUpCircle className="w-12 h-12 text-blue-500" />
            </div>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2 text-blue-500">
                <Crosshair className="w-4 h-4" />
                <span className="text-[10px] font-black uppercase tracking-wider">Target 2 (Extended)</span>
              </div>
              <div className="text-3xl font-mono font-black text-foreground mb-1 tabular-nums" data-testid="trade-setup-tp2">
                {parameters.take_profit_2.toLocaleString()}
              </div>
              <div className="flex items-center justify-between text-[10px] text-muted-foreground font-bold font-mono">
                <span>REWARD: {(((parameters.take_profit_2 - current_price) / current_price) * 100).toFixed(2)}%</span>
                <span className="text-blue-500/60 uppercase">RR 3.0x</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Zones List */}
        <div className="xl:col-span-8">
          <Card className="bg-card border-border h-full overflow-hidden">
            <div className="bg-muted/30 border-b border-border px-4 py-2 flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Liquidity & Rejection Zones</span>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5 font-bold text-[9px] text-destructive">
                  <div className="w-1.5 h-1.5 rounded-full bg-destructive" /> RESISTANCE
                </div>
                <div className="flex items-center gap-1.5 font-bold text-[9px] text-success">
                  <div className="w-1.5 h-1.5 rounded-full bg-success" /> SUPPORT
                </div>
              </div>
            </div>
            <CardContent className="p-0">
              <div className="grid grid-cols-2">
                {/* Resistance Side */}
                <div className="border-r border-border p-4 space-y-3">
                  {zones.resistance.slice().reverse().map((zone, idx) => (
                    <div key={idx} className="flex items-center justify-between group hover:bg-destructive/5 p-1 rounded transition-colors">
                      <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-destructive/80 font-mono tracking-tighter uppercase">{zone.label}</span>
                        <span className="text-[9px] text-muted-foreground font-bold uppercase">{zone.strength} REJECTION</span>
                      </div>
                      <div className="text-sm font-mono font-black tabular-nums border-b border-destructive/20">
                        {zone.level.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Support Side */}
                <div className="p-4 space-y-3">
                  {zones.support.map((zone, idx) => (
                    <div key={idx} className="flex items-center justify-between group hover:bg-success/5 p-1 rounded transition-colors">
                      <div className="text-sm font-mono font-black tabular-nums border-b border-success/20">
                        {zone.level.toLocaleString()}
                      </div>
                      <div className="flex flex-col text-right">
                        <span className="text-[10px] font-bold text-success/80 font-mono tracking-tighter uppercase">{zone.label}</span>
                        <span className="text-[9px] text-muted-foreground font-bold uppercase">{zone.strength} LIQUIDITY</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Risk Management Stats */}
        <div className="xl:col-span-4">
          <Card className="bg-card border-border h-full">
            <CardHeader className="py-3 border-b border-border">
              <CardTitle className="text-[10px] uppercase font-black tracking-widest text-muted-foreground flex items-center gap-2">
                <Scale className="w-3 h-3 text-primary" /> Setup Matrix
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-tight">ATR Volatility</span>
                <span className="text-xs font-mono font-black">{parameters.atr}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-tight">VaR Risk Cap</span>
                <span className="text-xs font-mono font-black">{parameters.var_risk}%</span>
              </div>
              <div className="flex items-center justify-between border-b border-border/50 pb-2">
                <span className="text-xs text-muted-foreground font-medium uppercase tracking-tight">Min R/R Ratio</span>
                <span className="text-xs font-mono font-black text-success">1 : {parameters.risk_reward_ratio}</span>
              </div>

              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 space-y-2">
                <div className="text-[10px] font-black text-primary uppercase tracking-wider">Recommended Sizing</div>
                <div className="flex items-end justify-between">
                  <span className="text-2xl font-mono font-black text-foreground">
                    {setup.position_sizing.recommended_shares.toLocaleString()}
                  </span>
                  <span className="text-[10px] font-bold text-muted-foreground uppercase">SHARES</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground font-bold">
                  <span>CAPITAL: ₹{(setup.position_sizing.capital_required / 1000).toFixed(1)}K</span>
                  <span>RISK: {setup.position_sizing.risk_per_trade_pct}%</span>
                </div>
              </div>

              <div className="pt-1">
                <div className="bg-muted p-2 rounded text-[10px] text-muted-foreground italic leading-snug">
                  Kelly Criterion suggests {setup.position_sizing.kelly_allocation_pct}% allocation. Sizing capped at {setup.position_sizing.risk_per_trade_pct}% account risk.
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
