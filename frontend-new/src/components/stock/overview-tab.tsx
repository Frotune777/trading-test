"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { PriceChart } from "@/components/stock/price-chart"
import { MetricsCard } from "@/components/stock/metrics-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface OverviewTabProps {
    symbol: string
}

interface PriceHistoryData {
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
}

export function OverviewTab({ symbol }: OverviewTabProps) {
    // Fetch historical price data
    const { data: priceHistory, isLoading: loadingHistory } = useQuery({
        queryKey: ['price-history', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}/history?days=365`)
            return res.data.data as PriceHistoryData[]
        },
        enabled: !!symbol
    })

    // Fetch stock snapshot for metrics
    const { data: stockData } = useQuery({
        queryKey: ['stock', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}`)
            return res.data
        },
        enabled: !!symbol
    })

    const snapshot = stockData?.snapshot || {}
    const profile = stockData?.profile || {}

    // Prepare metrics
    const valuationMetrics = [
        { label: 'P/E Ratio', value: snapshot.pe_ratio?.toFixed(2) },
        { label: 'P/B Ratio', value: snapshot.pb_ratio?.toFixed(2) },
        { label: 'Market Cap', value: snapshot.market_cap ? `₹${(snapshot.market_cap / 10000000).toFixed(0)}Cr` : '--' },
        { label: 'Book Value', value: snapshot.book_value ? `₹${snapshot.book_value.toFixed(2)}` : '--' },
    ]

    const performanceMetrics = [
        { label: 'ROE', value: snapshot.roe?.toFixed(2), suffix: '%' },
        { label: 'ROCE', value: snapshot.roce?.toFixed(2), suffix: '%' },
        { label: 'EPS', value: snapshot.eps ? `₹${snapshot.eps.toFixed(2)}` : '--' },
        { label: 'Dividend Yield', value: snapshot.dividend_yield?.toFixed(2), suffix: '%' },
    ]

    const companyInfo = [
        { label: 'Industry', value: profile.industry || '--' },
        { label: 'Sector', value: profile.sector || '--' },
        { label: 'ISIN', value: profile.isin || '--' },
        { label: 'Face Value', value: snapshot.face_value ? `₹${snapshot.face_value}` : '--' },
    ]

    if (loadingHistory) {
        return (
            <div className="space-y-4">
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[500px]" />
                <div className="grid gap-4 md:grid-cols-3">
                    <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[200px]" />
                    <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[200px]" />
                    <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[200px]" />
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Price Chart */}
            <PriceChart data={priceHistory || []} symbol={symbol} />

            {/* Metrics Grid */}
            <div className="grid gap-4 md:grid-cols-3">
                <MetricsCard title="Valuation Metrics" metrics={valuationMetrics} />
                <MetricsCard title="Performance Metrics" metrics={performanceMetrics} />
                <MetricsCard title="Company Info" metrics={companyInfo} />
            </div>

            {/* Corporate Actions */}
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Corporate Actions</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-sm text-slate-500">
                        No recent corporate actions available
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
