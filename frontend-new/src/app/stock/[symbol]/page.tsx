"use client"

import { useQuery } from "@tanstack/react-query"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { ArrowUpRight, ArrowDownRight, TrendingUp, Calendar, DollarSign, Activity } from "lucide-react"
import { cn } from "@/lib/utils"
import { OverviewTab } from "@/components/stock/overview-tab"
import { TechnicalTab } from "@/components/stock/technical-tab"
import { DerivativesTab } from "@/components/stock/derivatives-tab"
import { InsiderTab } from "@/components/stock/insider-tab"

interface StockProfile {
    symbol: string
    name: string
    sector?: string
    industry?: string
}

interface StockSnapshot {
    last_price: number
    change: number
    change_percent: number
    volume: number
    high_52w?: number
    low_52w?: number
    market_cap?: number
}

interface StockData {
    symbol: string
    profile: StockProfile
    snapshot: StockSnapshot
}

export default function StockPage() {
    const params = useParams()
    const symbol = params.symbol as string

    // Fetch stock profile and snapshot
    const { data: stockData, isLoading } = useQuery({
        queryKey: ['stock', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}`)
            return res.data as StockData
        },
        enabled: !!symbol
    })

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-slate-400">Loading {symbol}...</div>
            </div>
        )
    }

    if (!stockData) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-slate-400">Stock not found</div>
            </div>
        )
    }

    const { profile, snapshot } = stockData
    const isPositive = snapshot.change >= 0

    return (
        <div className="space-y-6">
            {/* Stock Header */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 backdrop-blur">
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-white">{symbol}</h1>
                            <Badge variant="outline" className="text-slate-400 border-slate-700">
                                {profile.sector || "Equity"}
                            </Badge>
                        </div>
                        <p className="text-slate-400 mt-1">{profile.name}</p>
                    </div>

                    <div className="text-right">
                        <div className="text-3xl font-bold text-white">
                            ₹{snapshot.last_price?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className={cn("flex items-center justify-end mt-1 text-sm font-medium",
                            isPositive ? "text-emerald-500" : "text-rose-500")}>
                            {isPositive ? <ArrowUpRight className="h-4 w-4 mr-1" /> : <ArrowDownRight className="h-4 w-4 mr-1" />}
                            {snapshot.change > 0 ? "+" : ""}{snapshot.change?.toFixed(2)} ({snapshot.change_percent?.toFixed(2)}%)
                        </div>
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
                    <div>
                        <div className="text-xs text-slate-500">Volume</div>
                        <div className="text-sm font-medium text-white mt-1">
                            {(snapshot.volume / 100000).toFixed(2)}L
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-500">52W High</div>
                        <div className="text-sm font-medium text-white mt-1">
                            ₹{snapshot.high_52w?.toLocaleString() || "--"}
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-500">52W Low</div>
                        <div className="text-sm font-medium text-white mt-1">
                            ₹{snapshot.low_52w?.toLocaleString() || "--"}
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-500">Market Cap</div>
                        <div className="text-sm font-medium text-white mt-1">
                            {snapshot.market_cap ? `₹${(snapshot.market_cap / 10000000).toFixed(0)}Cr` : "--"}
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabbed Content */}
            <Tabs defaultValue="overview" className="w-full">
                <TabsList className="bg-slate-900 border-slate-800 p-1">
                    <TabsTrigger value="overview" className="data-[state=active]:bg-slate-800">Overview</TabsTrigger>
                    <TabsTrigger value="technicals" className="data-[state=active]:bg-slate-800">Technicals</TabsTrigger>
                    <TabsTrigger value="derivatives" className="data-[state=active]:bg-slate-800">Derivatives</TabsTrigger>
                    <TabsTrigger value="insider" className="data-[state=active]:bg-slate-800">Insider</TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-4 mt-4">
                    <OverviewTab symbol={symbol} />
                </TabsContent>

                {/* Technicals Tab */}
                <TabsContent value="technicals" className="space-y-4 mt-4">
                    <TechnicalTab symbol={symbol} />
                </TabsContent>

                {/* Derivatives Tab */}
                <TabsContent value="derivatives" className="space-y-4 mt-4">
                    <DerivativesTab symbol={symbol} />
                </TabsContent>

                {/* Insider Tab */}
                <TabsContent value="insider" className="space-y-4 mt-4">
                    <InsiderTab symbol={symbol} />
                </TabsContent>
            </Tabs>
        </div>
    )
}
