"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

export function MarketBreadthWidget() {
    const { data: breadthData, isLoading } = useQuery({
        queryKey: ['market-breadth'],
        queryFn: async () => {
            const res = await api.get('/market/breadth')
            return res.data.data
        }
    })

    if (isLoading) {
        return (
            <Card className="col-span-3 bg-slate-900/50 border-slate-800 animate-pulse h-[300px]" />
        )
    }

    if (!breadthData) {
        return (
            <Card className="col-span-3 bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Market Breadth</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No market breadth data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    const advances = breadthData.advances || 0
    const declines = breadthData.declines || 0
    const unchanged = breadthData.unchanged || 0
    const total = advances + declines + unchanged

    const advancePercent = total > 0 ? (advances / total) * 100 : 0
    const declinePercent = total > 0 ? (declines / total) * 100 : 0
    const ratio = declines > 0 ? (advances / declines).toFixed(2) : 'N/A'

    const isBullish = advances > declines

    return (
        <Card className="col-span-3 bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">Market Breadth</CardTitle>
            </CardHeader>
            <CardContent>
                {/* Ratio Display */}
                <div className="text-center mb-6">
                    <div className="text-4xl font-bold text-white mb-2">
                        {ratio}
                    </div>
                    <div className="text-sm text-slate-400">Advance/Decline Ratio</div>
                    <div className={`text-xs mt-1 flex items-center justify-center ${isBullish ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {isBullish ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                        {isBullish ? 'Bullish Market' : 'Bearish Market'}
                    </div>
                </div>

                {/* Advances */}
                <div className="space-y-4">
                    <div>
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-emerald-500 font-medium">Advances</span>
                            <span className="text-white font-medium">{advances} ({advancePercent.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-3">
                            <div
                                className="bg-emerald-500 h-3 rounded-full transition-all duration-500"
                                style={{ width: `${advancePercent}%` }}
                            />
                        </div>
                    </div>

                    {/* Declines */}
                    <div>
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-rose-500 font-medium">Declines</span>
                            <span className="text-white font-medium">{declines} ({declinePercent.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-3">
                            <div
                                className="bg-rose-500 h-3 rounded-full transition-all duration-500"
                                style={{ width: `${declinePercent}%` }}
                            />
                        </div>
                    </div>

                    {/* Unchanged */}
                    {unchanged > 0 && (
                        <div className="flex justify-between text-sm text-slate-400">
                            <span>Unchanged</span>
                            <span>{unchanged}</span>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
