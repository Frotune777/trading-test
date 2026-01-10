"use client"

import { QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { MarketProvider } from "@/context/market-context"
import { AuthProvider } from "@/context/auth-context"
import { ThemeProvider } from "./theme-provider"
import { queryClient } from "@/lib/query-client"

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <ThemeProvider defaultTheme="dark" storageKey="trading-theme">
                    <MarketProvider>
                        {children}
                    </MarketProvider>
                </ThemeProvider>
            </AuthProvider>
            {process.env.NODE_ENV === 'development' && (
                <ReactQueryDevtools initialIsOpen={false} />
            )}
        </QueryClientProvider>
    )
}
