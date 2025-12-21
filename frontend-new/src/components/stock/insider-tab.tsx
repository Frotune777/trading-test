"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { InsiderTradesTable } from "./insider-trades-table"
import { BulkDealsTable } from "./bulk-deals-table"
import { BlockDealsTable } from "./block-deals-table"
import { Card } from "@/components/ui/card"

interface InsiderTabProps {
    symbol: string
}

export function InsiderTab({ symbol }: InsiderTabProps) {
    // Fetch insider trades
    const { data: insiderTrades, isLoading: loadingInsider } = useQuery({
        queryKey: ['insider-trades'],
        queryFn: async () => {
            // Get last 30 days of data
            const toDate = new Date()
            const fromDate = new Date()
            fromDate.setDate(fromDate.getDate() - 30)

            const res = await api.get(`/insider/trades`, {
                params: {
                    from_date: fromDate.toISOString().split('T')[0],
                    to_date: toDate.toISOString().split('T')[0]
                }
            })
            return res.data.data
        }
    })

    // Fetch bulk deals
    const { data: bulkDeals, isLoading: loadingBulk } = useQuery({
        queryKey: ['bulk-deals'],
        queryFn: async () => {
            // Get last 30 days of data
            const toDate = new Date()
            const fromDate = new Date()
            fromDate.setDate(fromDate.getDate() - 30)

            const res = await api.get(`/insider/bulk-deals`, {
                params: {
                    from_date: fromDate.toISOString().split('T')[0],
                    to_date: toDate.toISOString().split('T')[0]
                }
            })
            return res.data.data
        }
    })

    // Fetch block deals
    const { data: blockDeals, isLoading: loadingBlock } = useQuery({
        queryKey: ['block-deals'],
        queryFn: async () => {
            const toDate = new Date()
            const fromDate = new Date()
            fromDate.setDate(fromDate.getDate() - 30)

            const res = await api.get(`/insider/block-deals`, {
                params: {
                    from_date: fromDate.toISOString().split('T')[0],
                    to_date: toDate.toISOString().split('T')[0]
                }
            })
            return res.data.data
        }
    })

    if (loadingInsider || loadingBulk || loadingBlock) {
        return (
            <div className="space-y-4">
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
                <Card className="bg-slate-900/50 border-slate-800 animate-pulse h-[400px]" />
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Insider Trades */}
            <InsiderTradesTable data={insiderTrades} symbol={symbol} />

            {/* Bulk Deals */}
            <BulkDealsTable data={bulkDeals} symbol={symbol} />

            {/* Block Deals */}
            <BlockDealsTable data={blockDeals} symbol={symbol} />
        </div>
    )
}
