'use client';

import { useState, useCallback } from 'react';
import { TradeIntentResponse, DecisionStatistics, ConvictionTimeline } from '@/lib/api/types';
import QuadService from '@/lib/api/quad';

interface UseQuadAnalyticsReturn {
  reasoning: TradeIntentResponse | null;
  statistics: DecisionStatistics | null;
  timeline: ConvictionTimeline | null;
  loading: boolean;
  error: string | null;
  fetchAll: (symbol: string) => Promise<void>;
}

export function useQuadAnalytics(): UseQuadAnalyticsReturn {
  const [reasoning, setReasoning] = useState<TradeIntentResponse | null>(null);
  const [statistics, setStatistics] = useState<DecisionStatistics | null>(null);
  const [timeline, setTimeline] = useState<ConvictionTimeline | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async (symbol: string) => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch in parallel
      const [res, stats, time] = await Promise.all([
        QuadService.getAnalysis(symbol),
        QuadService.getStatistics(symbol),
        QuadService.getConvictionTimeline(symbol, 30)
      ]);

      setReasoning(res);
      setStatistics(stats);
      setTimeline(time);
    } catch (err) {
      console.error('Error fetching QUAD analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch QUAD analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    reasoning,
    statistics,
    timeline,
    loading,
    error,
    fetchAll,
  };
}
