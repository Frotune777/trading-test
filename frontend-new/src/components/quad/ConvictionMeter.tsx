'use client';

/**
 * ConvictionMeter Component
 * 
 * Displays overall conviction score (0-100) with:
 * - Circular gauge visualization
 * - Execution readiness status
 * - Directional bias indicator
 * - Contract version display
 * 
 * CRITICAL: This is ANALYSIS ONLY, not execution authorization
 * Maps to: conviction_score, directional_bias, is_execution_ready from TradeIntent v1.0
 */

import React from 'react';
import { DirectionalBias, PillarContribution } from '@/types/quad';
import { cn } from '@/lib/utils';
import { Tooltip } from '@/components/ui/tooltip';

import {
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Info,
} from 'lucide-react';

interface ConvictionMeterProps {
  conviction: number; // 0-100
  directionalBias: DirectionalBias;
  isExecutionReady: boolean;
  contractVersion?: string;
  pillarContributions?: PillarContribution[];
  reasoning?: string;
}

export function ConvictionMeter({
  conviction,
  directionalBias,
  isExecutionReady,
  contractVersion = '1.0.0',
  pillarContributions = [],
  reasoning,
}: ConvictionMeterProps) {
  // Helper to get conviction level label
  const getConvictionLabel = (score: number): string => {
    if (score >= 80) return 'Very High';
    if (score >= 65) return 'High';
    if (score >= 50) return 'Moderate';
    if (score >= 35) return 'Low';
    return 'Very Low';
  };

  // Helper to get conviction color
  const getConvictionColor = (score: number): string => {
    if (score >= 70) return 'text-success';
    if (score >= 50) return 'text-warning';
    if (score >= 30) return 'text-warning/80';
    return 'text-destructive';
  };

  // Helper to get bias styling
  const getBiasStyle = (bias: DirectionalBias) => {
    switch (bias) {
      case 'BULLISH':
        return {
          color: 'text-success',
          bgColor: 'bg-success/10',
          borderColor: 'border-success/20',
          icon: <TrendingUp className="w-5 h-5" />,
        };
      case 'BEARISH':
        return {
          color: 'text-destructive',
          bgColor: 'bg-destructive/10',
          borderColor: 'border-destructive/20',
          icon: <TrendingDown className="w-5 h-5" />,
        };
      case 'INVALID':
        return {
          color: 'text-muted-foreground',
          bgColor: 'bg-muted',
          borderColor: 'border-border',
          icon: <XCircle className="w-5 h-5" />,
        };
      default:
        return {
          color: 'text-muted-foreground',
          bgColor: 'bg-muted',
          borderColor: 'border-border',
          icon: <Minus className="w-5 h-5" />,
        };
    }
  };

  const biasStyle = getBiasStyle(directionalBias);

  // Calculate gauge dimensions
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (conviction / 100) * circumference;

  return (
    <div className="w-full bg-card rounded-lg border border-border p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-foreground">
            Analysis Conviction
          </h3>
          {pillarContributions.length > 0 && (
            <Tooltip
              content={
                <div className="space-y-3">
                  <div className="font-semibold text-sm border-b border-border pb-2">
                    Pillar Breakdown
                  </div>
                  {pillarContributions.map((pillar) => (
                    <div key={pillar.name} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">
                          {pillar.name}
                        </span>
                        <span className={cn(
                          "text-sm font-semibold",
                          pillar.score >= 70 ? "text-success" :
                            pillar.score >= 50 ? "text-warning" :
                              "text-destructive"
                        )}>
                          {pillar.score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          Bias: <span className={cn(
                            "font-medium",
                            pillar.bias === 'BULLISH' ? "text-success" :
                              pillar.bias === 'BEARISH' ? "text-destructive" :
                                "text-muted-foreground"
                          )}>{pillar.bias}</span>
                        </span>
                        <span className="text-muted-foreground">
                          Weight: {(pillar.weight_applied * 100).toFixed(0)}%
                        </span>
                      </div>
                      {pillar.explanation && (
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {pillar.explanation}
                        </p>
                      )}
                    </div>
                  ))}
                  {reasoning && (
                    <div className="pt-2 border-t border-border">
                      <div className="text-xs font-medium mb-1">Overall Reasoning</div>
                      <p className="text-xs text-muted-foreground">{reasoning}</p>
                    </div>
                  )}
                </div>
              }
            >
              <Info className="w-4 h-4 text-muted-foreground hover:text-foreground transition-colors" />
            </Tooltip>
          )}
        </div>
        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
          v{contractVersion}
        </span>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-8">
        {/* Circular Gauge */}
        <div className="relative">
          <svg width="200" height="200" className="transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="100"
              cy="100"
              r={radius}
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              className="text-muted"
            />
            {/* Progress circle */}
            <circle
              cx="100"
              cy="100"
              r={radius}
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={cn(
                "transition-all duration-1000 ease-out",
                conviction >= 70 ? 'text-success' :
                  conviction >= 50 ? 'text-warning' :
                    conviction >= 30 ? 'text-warning/80' : 'text-destructive'
              )}
            />
          </svg>

          {/* Center Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold ${getConvictionColor(conviction)}`} data-testid="conviction-score">
              {conviction.toFixed(1)}%
            </span>
            <span className="text-sm text-muted-foreground mt-1" data-testid="conviction-label">
              {getConvictionLabel(conviction)}
            </span>
          </div>
        </div>

        {/* Details Panel */}
        <div className="flex-1 space-y-4">
          {/* Directional Bias */}
          <div
            className={`flex items-center justify-between p-4 rounded-lg border ${biasStyle.borderColor} ${biasStyle.bgColor}`}
          >
            <div className="flex items-center gap-3">
              <div className={biasStyle.color}>{biasStyle.icon}</div>
              <div>
                <div className="text-sm text-gray-600">Directional Bias</div>
                <div className={`text-lg font-semibold ${biasStyle.color}`} data-testid="conviction-bias">
                  {directionalBias}
                </div>
              </div>
            </div>
          </div>

          {/* Execution Readiness */}
          <div
            className={`flex items-center justify-between p-4 rounded-lg border ${isExecutionReady
              ? 'border-success/20 bg-success/10'
              : 'border-warning/20 bg-warning/10'
              }`}
          >
            <div className="flex items-center gap-3">
              <div className={isExecutionReady ? 'text-success' : 'text-warning'}>
                {isExecutionReady ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertTriangle className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className="text-sm text-foreground/60">Execution Status</div>
                <div
                  className={`text-lg font-semibold ${isExecutionReady ? 'text-success' : 'text-warning'
                    }`}
                  data-testid="execution-ready-status"
                >
                  {isExecutionReady ? 'Ready' : 'Not Ready'}
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-4 p-3 bg-primary/10 border border-primary/20 rounded-lg">
            <p className="text-xs text-primary/80">
              <strong>Note:</strong> This is analysis only, not trading advice. Conviction
              score represents confidence in the reasoning, not position sizing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
