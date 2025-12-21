"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { TechnicalIndicatorsTable } from "./technical-indicators-table"
import { IntradayChart } from "./intraday-chart"
import { Card } from "@/components/ui/card"

interface TechnicalTabProps {
    symbol: string
}

export function TechnicalTab({ symbol }: TechnicalTabProps) {
    const [interval, setInterval] = useState('5m')

    // Fetch technical indicators
    const { data: technicalData, isLoading: loadingIndicators } = useQuery({
        queryKey: ['technical-indicators', symbol],
        queryFn: async () => {
            const res = await api.get(`/technicals/indicators/${symbol}`)
            return res.data
        },
        enabled: !!symbol
    })

    // Fetch intraday data
    const { data: intradayData, isLoading: loadingIntraday } = useQuery({
        queryKey: ['intraday', symbol, interval],
        queryFn: async () => {
            const res = await api.get(`/technicals/intraday/${symbol}?interval=${interval}`)
            return res.data.data
        },
        enabled: !!symbol
    })

    if (loadingIndicators || loadingIntraday) {
        return (
            <div className="space-y-4">
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[500px]" />
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Intraday Chart */}
            <IntradayChart
                data={intradayData || []}
                symbol={symbol}
                onIntervalChange={setInterval}
            />

            {/* Technical Indicators */}
            <TechnicalIndicatorsTable
                indicators={technicalData?.indicators || []}
                stats={technicalData?.stats || {}}
            />
        </div>
    )
}
