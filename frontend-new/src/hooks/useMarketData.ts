/**
 * React Hook for WebSocket Market Data
 * Provides real-time market data with automatic subscription management
 */

import { useEffect, useState, useCallback } from 'react';
import { getWebSocketService, MarketTick } from '@/services/websocket';

interface UseMarketDataOptions {
  symbols: string[];
  mode?: 'ltp' | 'quote' | 'full';
  enabled?: boolean;
}

interface MarketDataState {
  data: Record<string, MarketTick>;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  error: Error | null;
}

export function useMarketData(options: UseMarketDataOptions) {
  const { symbols, mode = 'ltp', enabled = true } = options;

  const [state, setState] = useState<MarketDataState>({
    data: {},
    status: 'disconnected',
    error: null,
  });

  useEffect(() => {
    if (!enabled || symbols.length === 0) {
      return;
    }

    const ws = getWebSocketService();

    // Status handler
    const unsubStatus = ws.onStatus((status) => {
      setState((prev) => ({ ...prev, status }));
    });

    // Error handler
    const unsubError = ws.onError((error) => {
      setState((prev) => ({ ...prev, error }));
    });

    // Message handler
    const unsubMessage = ws.onMessage((tick) => {
      setState((prev) => ({
        ...prev,
        data: {
          ...prev.data,
          [tick.symbol]: tick,
        },
      }));
    });

    // Connect and subscribe
    const init = async () => {
      try {
        if (!ws.isConnected()) {
          await ws.connect();
        }
        await ws.subscribe({ symbols, mode });
      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        setState((prev) => ({
          ...prev,
          error: error as Error,
          status: 'error',
        }));
      }
    };

    init();

    // Cleanup
    return () => {
      unsubStatus();
      unsubError();
      unsubMessage();
      ws.unsubscribe(symbols);
    };
  }, [symbols.join(','), mode, enabled]);

  const getLTP = useCallback(
    (symbol: string): number | null => {
      return state.data[symbol]?.ltp ?? null;
    },
    [state.data]
  );

  const getQuote = useCallback(
    (symbol: string): MarketTick | null => {
      return state.data[symbol] ?? null;
    },
    [state.data]
  );

  return {
    ...state,
    getLTP,
    getQuote,
  };
}
