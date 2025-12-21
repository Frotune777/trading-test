"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { OptionChain } from "./option-chain"
import { PCRChart } from "./pcr-chart"
import { FuturesDisplay } from "./futures-display"
import { Card } from "@/components/ui/card"

interface DerivativesTabProps {
    symbol: string
}

export function DerivativesTab({ symbol }: DerivativesTabProps) {
    // Fetch option chain
    const { data: optionChainData, isLoading: loadingOptionChain } = useQuery({
        queryKey: ['option-chain', symbol],
        queryFn: async () => {
            const res = await api.get(`/derivatives/option-chain/${symbol}?indices=true`)
            return res.data
        },
        enabled: !!symbol
    })

    // Fetch PCR
    const { data: pcrData, isLoading: loadingPCR } = useQuery({
        queryKey: ['pcr', symbol],
        queryFn: async () => {
            const res = await api.get(`/derivatives/pcr/${symbol}`)
            return res.data
        },
        enabled: !!symbol
    })

    // Fetch futures
    const { data: futuresData, isLoading: loadingFutures } = useQuery({
        queryKey: ['futures', symbol],
        queryFn: async () => {
            const res = await api.get(`/derivatives/futures/${symbol}`)
            return res.data.data
        },
        enabled: !!symbol
    })

    if (loadingOptionChain || loadingPCR || loadingFutures) {
        return (
            <div className="space-y-4">
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[600px]" />
                <div className="grid gap-4 md:grid-cols-2">
                    <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
                    <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Option Chain */}
            <OptionChain data={optionChainData} symbol={symbol} />

            {/* PCR and Futures */}
            <div className="grid gap-4 md:grid-cols-2">
                <PCRChart data={pcrData} symbol={symbol} />
                <FuturesDisplay data={futuresData} symbol={symbol} />
            </div>
        </div>
    )
}
