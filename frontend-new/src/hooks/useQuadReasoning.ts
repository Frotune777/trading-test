'use client';

/**
 * Custom React Hook for QUAD Reasoning Data
 * 
 * Provides easy-to-use interface for fetching and managing QUAD analytics data
 * Handles loading, error states, and caching
 */

import { useState, useCallback } from 'react';
import { ReasoningAPIResponse } from '@/types/quad';
import { API_ENDPOINTS, buildApiUrl } from '@/lib/api-config';

interface UseQuadReasoningReturn {
  data: ReasoningAPIResponse | null;
  loading: boolean;
  error: string | null;
  fetchReasoning: (symbol: string) => Promise<void>;
}

export function useQuadReasoning(): UseQuadReasoningReturn {
  const [data, setData] = useState<ReasoningAPIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReasoning = useCallback(async (symbol: string) => {
    if (!symbol) {
      setError('Symbol is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const url = buildApiUrl(API_ENDPOINTS.reasoning(symbol));
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const json = await response.json();
      setData(json);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reasoning data';
      setError(errorMessage);
      console.error('Error fetching QUAD reasoning:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    data,
    loading,
    error,
    fetchReasoning,
  };
}
