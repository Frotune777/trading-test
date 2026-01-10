import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            // Global defaults
            staleTime: 60_000,        // 1 minute
            gcTime: 300_000,          // 5 minutes (formerly cacheTime)
            retry: 2,
            refetchOnWindowFocus: false,
            refetchOnReconnect: true,
        },
    },
});

// Domain-specific configurations
export const queryConfigs = {
    // Real-time market data (prices, quotes)
    realtime: {
        staleTime: 5_000,           // 5 seconds
        gcTime: 30_000,             // 30 seconds
        refetchInterval: 10_000,    // Poll every 10s
        retry: 1,
    },

    // Static reference data (symbols, strategies)
    static: {
        staleTime: 3600_000,        // 1 hour
        gcTime: 86400_000,          // 24 hours
        retry: 3,
        refetchOnWindowFocus: false,
    },

    // Dashboard data (analytics, stats)
    dashboard: {
        staleTime: 30_000,          // 30 seconds
        gcTime: 300_000,            // 5 minutes
        retry: 2,
    },
};
