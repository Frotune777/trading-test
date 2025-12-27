'use client';

/**
 * PillarDashboard Component
 * 
 * Displays all 6 QUAD analytical pillars with:
 * - Score (0-100) as progress bar
 * - Bias color-coded (BULLISH=green, BEARISH=red, NEUTRAL=gray)
 * - Placeholder status indicator
 * - Weight applied in aggregation
 * 
 * Maps to: PillarContribution[] from TradeIntent v1.0
 */

import React from 'react';
import { PillarContribution } from '@/types/quad';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';

interface PillarDashboardProps {
  pillars: PillarContribution[];  // From API: pillar_contributions or pillar_scores
}

export function PillarDashboard({ pillars }: PillarDashboardProps) {
  // Helper to get bias color
  const getBiasColor = (bias: string): string => {
    switch (bias) {
      case 'BULLISH':
        return 'text-success bg-success/10';
      case 'BEARISH':
        return 'text-destructive bg-destructive/10';
      case 'VOLATILE':
        return 'text-warning bg-warning/10';
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  // Helper to get bias icon
  const getBiasIcon = (bias: string) => {
    switch (bias) {
      case 'BULLISH':
        return <TrendingUp className="w-4 h-4" />;
      case 'BEARISH':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  // Helper to get score color gradient
  const getScoreColor = (score: number): string => {
    if (score >= 70) return 'bg-success';
    if (score >= 50) return 'bg-warning';
    if (score >= 30) return 'bg-warning/80';
    return 'bg-destructive';
  };

  // State to track expanded card
  const [expandedPillar, setExpandedPillar] = React.useState<string | null>(null);

  // Pillar descriptions mapping
  const pillarDescriptions: Record<string, string> = {
    trend: "Evaluates the long-term direction using Moving Averages (SMA 50, SMA 200). A bullish trend indicates sustained upward price movement.",
    momentum: "Measures the speed of price changes using RSI and ROC. High momentum effectively captures strong buying pressure.",
    volatility: "Assesses price fluctuations using ATR and Bollinger Band Width. Neutral volatility is preferred for stable entry points.",
    liquidity: "Analyzes trading activity via Bid-Ask Spread and Market Depth. High liquidity ensures easy entry and exit with minimal slippage.",
    sentiment: "Gauges market mood using Put-Call Ratio (PCR) and Open Interest. Bullish sentiment suggests optimistic market participants.",
    regime: "Determines the broader market environment (e.g., Bull, Bear, Sideways) using VIX and localized trends."
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-foreground">
          QUAD Pillar Breakdown
        </h3>
        <span className="text-sm text-muted-foreground">
          {pillars.length} pillars analyzed
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {pillars.map((pillar) => {
          const isExpanded = expandedPillar === pillar.name;
          
          return (
            <div
              key={pillar.name}
              className={`bg-card rounded-lg border border-border p-4 hover:shadow-md transition-all cursor-pointer ${
                isExpanded ? 'ring-2 ring-primary shadow-md' : ''
              }`}
              data-testid="pillar-card"
              onClick={() => setExpandedPillar(isExpanded ? null : pillar.name)}
            >
              {/* Pillar Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-foreground capitalize">
                    {pillar.name}
                  </h4>
                  {pillar.is_placeholder && (
                    <span
                      className="px-2 py-0.5 text-xs rounded-full bg-warning/20 text-warning"
                      title="This pillar is returning neutral defaults"
                    >
                      <AlertCircle className="w-3 h-3 inline mr-1" />
                      Placeholder
                    </span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {(pillar.weight_applied * 100).toFixed(0)}% weight
                </span>
              </div>

              {/* Score Display */}
              <div className="mb-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-2xl font-bold text-foreground" data-testid="pillar-score">
                    {pillar.score.toFixed(1)}
                  </span>
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium ${getBiasColor(
                      pillar.bias
                    )}`}
                  >
                    {getBiasIcon(pillar.bias)}
                    {pillar.bias}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${getScoreColor(
                      pillar.score
                    )}`}
                    style={{ width: `${pillar.score}%` }}
                  />
                </div>
              </div>

              {/* Score Range Label */}
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>0</span>
                <span>50</span>
                <span>100</span>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-border text-sm text-muted-foreground animate-in fade-in slide-in-from-top-1">
                  <p className="font-semibold text-foreground mb-2">Key Metrics:</p>
                  {pillar.metrics && Object.keys(pillar.metrics).length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                       {Object.entries(pillar.metrics).map(([key, value]) => (
                         <div key={key} className="flex justify-between items-center bg-muted px-2 py-1 rounded">
                           <span className="text-xs text-muted-foreground">{key}</span>
                           <span className="text-sm font-medium text-foreground">{String(value)}</span>
                         </div>
                       ))}
                    </div>
                  ) : (
                    <p className="italic text-muted-foreground/60">No detailed metrics available.</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 bg-muted/50 rounded-lg">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-success" />
            <span className="text-muted-foreground">High Score (70-100)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-warning" />
            <span className="text-muted-foreground">Moderate (50-70)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-warning/60" />
            <span className="text-muted-foreground">Low (30-50)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-destructive" />
            <span className="text-muted-foreground">Very Low (0-30)</span>
          </div>
        </div>
      </div>
      
      <p className="text-xs text-muted-foreground/60 text-center mt-2">
        Click on any pillar card to see calculation details.
      </p>
    </div>
  );
}
