'use client';

import { useEffect, useState } from 'react';
import { quadAnalyticsAPI, CorrelationMatrix as CorrelationMatrixType } from '@/lib/api/quad-analytics-api';
import { Activity } from 'lucide-react';

interface CorrelationMatrixProps {
  symbol: string;
  days?: number;
}

export default function CorrelationMatrix({ symbol, days = 90 }: CorrelationMatrixProps) {
  const [matrix, setMatrix] = useState<CorrelationMatrixType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [symbol, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await quadAnalyticsAPI.getPillarCorrelations(symbol, days);
      setMatrix(data);
    } catch (error) {
      console.error('Error loading correlations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCorrelationColor = (correlation: number): string => {
    const abs = Math.abs(correlation);
    if (abs > 0.7) return correlation > 0 ? 'bg-green-600' : 'bg-red-600';
    if (abs > 0.4) return correlation > 0 ? 'bg-green-400' : 'bg-red-400';
    return 'bg-gray-300';
  };

  const getCorrelationText = (correlation: number): string => {
    const abs = Math.abs(correlation);
    if (abs > 0.7) return 'text-white font-bold';
    if (abs > 0.4) return 'text-gray-900 font-semibold';
    return 'text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  if (!matrix || matrix.correlations.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>Insufficient data for correlation analysis</p>
        <p className="text-sm mt-2">Need at least 10 historical data points</p>
      </div>
    );
  }

  const pillars = ['trend', 'momentum', 'volatility', 'liquidity', 'sentiment', 'regime'];
  
  // Build correlation map
  const corrMap: Record<string, Record<string, number>> = {};
  pillars.forEach(p1 => {
    corrMap[p1] = {};
    pillars.forEach(p2 => {
      if (p1 === p2) {
        corrMap[p1][p2] = 1.0;
      } else {
        const pair = matrix.correlations.find(
          c => (c.pillar1 === p1 && c.pillar2 === p2) || (c.pillar1 === p2 && c.pillar2 === p1)
        );
        corrMap[p1][p2] = pair ? pair.correlation : 0;
      }
    });
  });

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Pillar Correlation Matrix</h3>
        <p className="text-sm text-muted-foreground">
          Pearson correlation between pillars ({matrix.sample_size} samples, {matrix.days_analyzed} days)
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="border p-2 bg-muted"></th>
              {pillars.map(pillar => (
                <th key={pillar} className="border p-2 bg-muted text-xs capitalize">
                  {pillar}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pillars.map(pillar1 => (
              <tr key={pillar1}>
                <td className="border p-2 font-medium capitalize bg-muted">{pillar1}</td>
                {pillars.map(pillar2 => {
                  const corr = corrMap[pillar1][pillar2];
                  return (
                    <td 
                      key={pillar2}
                      className={`border p-2 text-center ${getCorrelationColor(corr)} ${getCorrelationText(corr)}`}
                    >
                      {corr.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="space-y-2">
        <div className="text-sm font-semibold">Interpretation:</div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-600 rounded"></div>
            <span>Strong Positive (&gt;0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span>Moderate Positive (0.4-0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-300 rounded"></div>
            <span>Weak (&lt;0.4)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span>Moderate Negative (-0.4 to -0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-600 rounded"></div>
            <span>Strong Negative (&lt;-0.7)</span>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Key Insights</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          {matrix.correlations
            .filter(c => Math.abs(c.correlation) > 0.7)
            .slice(0, 3)
            .map((c, idx) => (
              <li key={idx}>
                <strong>{c.pillar1}</strong> and <strong>{c.pillar2}</strong> are{' '}
                {c.correlation > 0 ? 'strongly correlated' : 'negatively correlated'}{' '}
                ({c.correlation.toFixed(2)})
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}
