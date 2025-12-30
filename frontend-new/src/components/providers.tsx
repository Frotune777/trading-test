"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import { MarketProvider } from "@/context/market-context"
import { AuthProvider } from "@/context/auth-context"
import { ThemeProvider } from "./theme-provider"

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60 * 1000,
                refetchOnWindowFocus: false,
            },
        },
    }))

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <ThemeProvider defaultTheme="dark" storageKey="trading-theme">
                    <MarketProvider>
                        {children}
                    </MarketProvider>
                </ThemeProvider>
            </AuthProvider>
        </QueryClientProvider>
    )
}
