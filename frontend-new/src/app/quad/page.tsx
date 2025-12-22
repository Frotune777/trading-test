'use client';

/**
 * QUAD Analytics Dashboard Page (Improved)
 * 
 * Uses custom hook for cleaner data management
 * Integrated with centralized API configuration
 */

import React, { useState, useEffect } from 'react';
import { PillarDashboard } from '@/components/quad/PillarDashboard';
import { ConvictionMeter } from '@/components/quad/ConvictionMeter';
import { WarningsPanel } from '@/components/quad/WarningsPanel';
import { PillarContribution } from '@/types/quad';
import { useQuadReasoning } from '@/hooks/useQuadReasoning';

export default function QUADDashboard() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const { data, loading, error, fetchReasoning } = useQuadReasoning();

  // Initial fetch on mount
  useEffect(() => {
    fetchReasoning(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Handle form submission
  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    fetchReasoning(symbol);
  };

  // Convert pillar_scores object to PillarContribution array
  const getPillarContributions = (): PillarContribution[] => {
    if (!data || !data.pillar_scores) return [];

    return Object.entries(data.pillar_scores).map(([name, pillar]) => ({
      name,
      score: pillar.score,
      bias: pillar.bias as 'BULLISH' | 'BEARISH' | 'NEUTRAL',
      is_placeholder: pillar.is_placeholder,
      weight_applied: pillar.weight,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            QUAD Reasoning Analytics
          </h1>
          <p className="text-gray-600">
            Multi-dimensional market analysis using 6 quantitative pillars
          </p>
        </div>

        {/* Symbol Input Form */}
        <form onSubmit={handleAnalyze} className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-2">
                Stock Symbol
              </label>
              <input
                id="symbol"
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="Enter symbol (e.g., RELIANCE, TCS, INFY)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !symbol}
              className="mt-7 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </form>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Analyzing {symbol}...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-red-600 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="text-red-800 font-medium">Error</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Data Display */}
        {data && !loading && (
          <div className="space-y-6">
            {/* Reasoning Narrative */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">
                  Reasoning Summary
                </h3>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {data.symbol}
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed">{data.reasoning}</p>
              <div className="mt-4 text-sm text-gray-500 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Analyzed: {new Date(data.analysis_timestamp).toLocaleString()}
              </div>
            </div>

            {/* Conviction Meter */}
            <ConvictionMeter
              conviction={data.conviction_score}
              directionalBias={data.directional_bias}
              isExecutionReady={data.is_execution_ready}
              contractVersion={data.contract_version}
            />

            {/* Warnings Panel */}
            <WarningsPanel warnings={data.warnings} quality={data.quality} />

            {/* Pillar Dashboard */}
            <PillarDashboard pillars={getPillarContributions()} />

            {/* Market Context (Optional) */}
            {data.market_context && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Market Context
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <span className="text-xs text-gray-600 block mb-1">Regime</span>
                    <span className="font-medium text-gray-900 text-lg">
                      {data.market_context.regime}
                    </span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <span className="text-xs text-gray-600 block mb-1">VIX Level</span>
                    <span className="font-medium text-gray-900 text-lg">
                      {data.market_context.vix_level.toFixed(2)}
                    </span>
                  </div>
                  {data.technical_state && (
                    <>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <span className="text-xs text-gray-600 block mb-1">LTP</span>
                        <span className="font-medium text-gray-900 text-lg">
                          ₹{data.technical_state.ltp.toFixed(2)}
                        </span>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <span className="text-xs text-gray-600 block mb-1">RSI</span>
                        <span className="font-medium text-gray-900 text-lg">
                          {data.technical_state.rsi.toFixed(1)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!data && !loading && !error && (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <svg
              className="w-16 h-16 text-gray-400 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Enter a stock symbol to begin analysis
            </h3>
            <p className="text-gray-600">
              The QUAD system will analyze 6 analytical dimensions and provide comprehensive insights
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
