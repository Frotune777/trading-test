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
import { DirectionalBias } from '@/types/quad';
import {
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
} from 'lucide-react';

interface ConvictionMeterProps {
  conviction: number; // 0-100
  directionalBias: DirectionalBias;
  isExecutionReady: boolean;
  contractVersion?: string;
}

export function ConvictionMeter({
  conviction,
  directionalBias,
  isExecutionReady,
  contractVersion = '1.0.0',
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
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    if (score >= 30) return 'text-orange-600';
    return 'text-red-600';
  };

  // Helper to get bias styling
  const getBiasStyle = (bias: DirectionalBias) => {
    switch (bias) {
      case 'BULLISH':
        return {
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          icon: <TrendingUp className="w-5 h-5" />,
        };
      case 'BEARISH':
        return {
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          icon: <TrendingDown className="w-5 h-5" />,
        };
      case 'INVALID':
        return {
          color: 'text-gray-400',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          icon: <XCircle className="w-5 h-5" />,
        };
      default:
        return {
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
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
    <div className="w-full bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Analysis Conviction
        </h3>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
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
              stroke="#e5e7eb"
              strokeWidth="12"
              fill="none"
            />
            {/* Progress circle */}
            <circle
              cx="100"
              cy="100"
              r={radius}
              stroke={
                conviction >= 70
                  ? '#10b981'
                  : conviction >= 50
                  ? '#eab308'
                  : conviction >= 30
                  ? '#f97316'
                  : '#ef4444'
              }
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Center Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold ${getConvictionColor(conviction)}`}>
              {conviction.toFixed(1)}%
            </span>
            <span className="text-sm text-gray-500 mt-1">
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
                <div className={`text-lg font-semibold ${biasStyle.color}`}>
                  {directionalBias}
                </div>
              </div>
            </div>
          </div>

          {/* Execution Readiness */}
          <div
            className={`flex items-center justify-between p-4 rounded-lg border ${
              isExecutionReady
                ? 'border-green-200 bg-green-50'
                : 'border-yellow-200 bg-yellow-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={isExecutionReady ? 'text-green-600' : 'text-yellow-600'}>
                {isExecutionReady ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertTriangle className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className="text-sm text-gray-600">Execution Status</div>
                <div
                  className={`text-lg font-semibold ${
                    isExecutionReady ? 'text-green-600' : 'text-yellow-600'
                  }`}
                >
                  {isExecutionReady ? 'Ready' : 'Not Ready'}
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong> This is analysis only, not trading advice. Conviction
              score represents confidence in the reasoning, not position sizing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
