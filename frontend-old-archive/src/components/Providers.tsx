'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useState } from 'react';
import AlertListener from './risk/AlertListener';
import ErrorBoundary from './common/ErrorBoundary';
import CommandPalette from './common/CommandPalette';

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60 * 1000, // 1 minute
                retry: 1,
            },
        },
    }));

    return (
        <QueryClientProvider client={queryClient}>
            <ErrorBoundary>
                {children}
                <AlertListener />
                <CommandPalette />
                <Toaster
                    position="top-right"
                    toastOptions={{
                        duration: 4000,
                        style: {
                            background: '#1F2937',
                            color: '#F3F4F6',
                            border: '1px solid #374151',
                        },
                        success: {
                            iconTheme: {
                                primary: '#10B981',
                                secondary: '#F3F4F6',
                            },
                        },
                        error: {
                            iconTheme: {
                                primary: '#EF4444',
                                secondary: '#F3F4F6',
                            },
                        },
                    }}
                />
            </ErrorBoundary>
        </QueryClientProvider>
    );
}
