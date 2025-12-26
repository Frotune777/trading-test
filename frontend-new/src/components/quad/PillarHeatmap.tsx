'use client';

import { useEffect, useState } from 'react';
import { quadAnalyticsAPI, QUADDecision } from '@/lib/api/quad-analytics-api';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface PillarHeatmapProps {
  symbol: string;
  days?: number;
}

export default function PillarHeatmap({ symbol, days = 30 }: PillarHeatmapProps) {
  const [decisions, setDecisions] = useState<QUADDecision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [symbol, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      const history = await quadAnalyticsAPI.getDecisionHistory(symbol, { limit: 10 });
      setDecisions(history.reverse()); // Oldest first
    } catch (error) {
      console.error('Error loading pillar data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 70) return 'bg-green-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreText = (score: number): string => {
    if (score >= 70) return 'text-green-900';
    if (score >= 40) return 'text-yellow-900';
    return 'text-red-900';
  };

  const getTrendIcon = (current: number, previous: number | undefined) => {
    if (!previous) return <Minus className="w-3 h-3" />;
    if (current > previous) return <TrendingUp className="w-3 h-3 text-green-600" />;
    if (current < previous) return <TrendingDown className="w-3 h-3 text-red-600" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  if (decisions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No historical data available</p>
      </div>
    );
  }

  const pillars = ['trend', 'momentum', 'volatility', 'liquidity', 'sentiment', 'regime'] as const;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Pillar Heatmap</h3>
        <p className="text-sm text-muted-foreground">
          Track pillar score evolution over time
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="border p-2 text-left bg-muted">Pillar</th>
              {decisions.map((decision, idx) => (
                <th key={idx} className="border p-2 text-center bg-muted text-xs">
                  {new Date(decision.timestamp).toLocaleDateString()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pillars.map((pillar) => (
              <tr key={pillar}>
                <td className="border p-2 font-medium capitalize">{pillar}</td>
                {decisions.map((decision, idx) => {
                  const score = decision.pillars[pillar];
                  const prevScore = idx > 0 ? decisions[idx - 1].pillars[pillar] : undefined;
                  
                  return (
                    <td 
                      key={idx} 
                      className={`border p-2 text-center relative group ${getScoreColor(score)} bg-opacity-20`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <span className={`font-semibold ${getScoreText(score)}`}>
                          {score}
                        </span>
                        {getTrendIcon(score, prevScore)}
                      </div>
                      
                      {/* Tooltip */}
                      <div className="absolute hidden group-hover:block bg-black text-white text-xs rounded p-2 z-10 -top-12 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                        {pillar}: {score}
                        {prevScore !== undefined && (
                          <div>Change: {score - prevScore > 0 ? '+' : ''}{score - prevScore}</div>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Strong (70-100)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span>Neutral (40-69)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Weak (0-39)</span>
        </div>
      </div>
    </div>
  );
}
