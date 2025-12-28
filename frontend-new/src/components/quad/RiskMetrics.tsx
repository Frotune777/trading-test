'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '../ui/card';
import { 
  ShieldAlert, 
  TrendingUp, 
  Award, 
  Activity,
  Info,
  ChevronRight,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { riskAPI, FullRiskMetrics } from '@/lib/api/risk-api';

interface RiskMetricsProps {
  symbol: string;
}

export default function RiskMetrics({ symbol }: RiskMetricsProps) {
  const [metrics, setMetrics] = useState<FullRiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRisk() {
      try {
        setLoading(true);
        // Try getting latest metrics first, if fails, calculate them
        let data;
        try {
          data = await riskAPI.getLatestMetrics(symbol);
        } catch (e) {
          data = await riskAPI.getAllMetrics(symbol);
        }
        setMetrics(data);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching risk metrics:', err);
        setError(err.message || 'Failed to load risk metrics');
      } finally {
        setLoading(false);
      }
    }

    if (symbol) {
      fetchRisk();
    }
  }, [symbol]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-[120px]">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse bg-card border-border border-dashed h-full flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
          </Card>
        ))}
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <Card className="bg-destructive/5 border-destructive/20 p-6 flex flex-col items-center justify-center text-center">
        <AlertTriangle className="w-8 h-8 text-destructive mb-2" />
        <h4 className="text-sm font-bold text-destructive uppercase tracking-wider">Risk Data Unavailable</h4>
        <p className="text-xs text-muted-foreground mt-1 max-w-md">
          Historical price data for {symbol} is currently being synchronized. 
          Please try again in a few minutes.
        </p>
      </Card>
    );
  }

  // Formatters with null checks
  const getVaR = () => metrics.var['95_30d'] ?? 0;
  const getBeta = () => metrics.beta['252d'] ?? 0;
  const getSharpe = () => metrics.sharpe['252d'] ?? 0;
  const getVol = () => metrics.volatility['252d'] ?? 0;

  const vaRValue = getVaR();
  const betaValue = getBeta();
  const sharpeValue = getSharpe();
  const volValue = getVol();

  // Interpretations
  const getVaRLevel = (val: number) => {
    const absVal = Math.abs(val);
    if (absVal < 1.0) return { label: 'LOW', color: 'text-success' };
    if (absVal < 2.5) return { label: 'MODERATE', color: 'text-warning' };
    return { label: 'HIGH', color: 'text-destructive' };
  };

  const getBetaLevel = (val: number) => {
    if (val < 0.8) return { label: 'DEFENSIVE', color: 'text-success' };
    if (val <= 1.2) return { label: 'ALIGNED', color: 'text-blue-500' };
    return { label: 'AGGRESSIVE', color: 'text-destructive' };
  };

  const getSharpeRating = (val: number) => {
    if (val < 0) return { label: 'POOR', color: 'text-destructive' };
    if (val < 1) return { label: 'SUB-PAR', color: 'text-warning' };
    if (val < 2) return { label: 'GOOD', color: 'text-success' };
    return { label: 'EXCEPTIONAL', color: 'text-blue-400' };
  };

  const varInfo = getVaRLevel(vaRValue);
  const betaInfo = getBetaLevel(betaValue);
  const sharpeInfo = getSharpeRating(sharpeValue);

  const metricCards = [
    {
      id: 'var',
      title: 'Value at Risk (VaR)',
      value: `${vaRValue.toFixed(2)}%`,
      subValue: '95% CONF / 30D',
      label: varInfo.label,
      labelColor: varInfo.color,
      icon: <ShieldAlert className="w-4 h-4" />,
      description: `Max expected 1-day loss is ${Math.abs(vaRValue).toFixed(2)}% under normal market conditions.`
    },
    {
      id: 'beta',
      title: 'Market Beta',
      value: betaValue.toFixed(2),
      subValue: 'VS NIFTY 50 / 252D',
      label: betaInfo.label,
      labelColor: betaInfo.color,
      icon: <Activity className="w-4 h-4" />,
      description: betaValue > 1 
        ? `Stock is ${((betaValue - 1) * 100).toFixed(0)}% more volatile than the market.`
        : `Stock is ${((1 - betaValue) * 100).toFixed(0)}% less volatile than the market.`
    },
    {
      id: 'sharpe',
      title: 'Sharpe Ratio',
      value: sharpeValue.toFixed(2),
      subValue: 'RISK-ADJUSTED RET',
      label: sharpeInfo.label,
      labelColor: sharpeInfo.color,
      icon: <Award className="w-4 h-4" />,
      description: sharpeValue > 1
        ? "Excellent risk-adjusted returns compared to risk-free rate."
        : "Returns are not adequately compensating for the risk taken."
    },
    {
      id: 'volatility',
      title: 'Volatility (σ)',
      value: `${volValue.toFixed(1)}%`,
      subValue: 'ANNUALIZED / 252D',
      label: volValue > 25 ? 'HIGH' : volValue > 15 ? 'NORMAL' : 'LOW',
      labelColor: volValue > 25 ? 'text-destructive' : volValue > 15 ? 'text-warning' : 'text-success',
      icon: <TrendingUp className="w-4 h-4" />,
      description: `Annual price variation of ${volValue.toFixed(1)}% based on historical standard deviation.`
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-[0.2em] font-black text-muted-foreground">Institutional Risk Metrics</h3>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
            <Info className="w-3 h-3" /> BASED ON {metrics.data_points_used} HISTORICAL SESSIONS
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((card) => (
          <Card key={card.id} className="bg-card border-border hover:border-sidebar-accent transition-all group overflow-hidden relative">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-muted rounded border border-border text-muted-foreground group-hover:text-foreground transition-colors">
                    {card.icon}
                  </div>
                  <div>
                    <div className="text-[10px] font-black text-muted-foreground uppercase tracking-wider leading-none mb-1">
                      {card.title}
                    </div>
                    <div className="text-[9px] font-mono text-muted-foreground/70 tracking-tighter uppercase leading-none">
                      {card.subValue}
                    </div>
                  </div>
                </div>
                <div className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded bg-muted/50 border border-border", card.labelColor)}>
                  {card.label}
                </div>
              </div>

              <div className="text-3xl font-mono font-black text-foreground mb-4 tabular-nums">
                {card.value}
              </div>

              <div className="h-px bg-border/50 mb-3" />
              
              <div className="text-[10px] text-muted-foreground h-8 leading-tight italic group-hover:text-foreground transition-colors">
                {card.description}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
