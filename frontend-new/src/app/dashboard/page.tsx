"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUpRight, ArrowDownRight, TrendingUp, Activity } from "lucide-react"
import { cn } from "@/lib/utils"
import { MarketBreadthWidget } from "@/components/dashboard/market-breadth-widget"

// Types based on API responses
interface IndexData {
    name: string
    value: number
    change: number
    change_percent: number
    is_up: boolean
}

interface StockActivity {
    symbol: string
    lastPrice: number
    pChange: number
    totalTradedVolume: number
}

export default function DashboardPage() {

    // Query 1: Market Indices
    const { data: indices, isLoading: loadingIndices } = useQuery({
        queryKey: ['market-indices'],
        queryFn: async () => {
            const res = await api.get('/market/indices')
            return res.data.data as IndexData[]
        }
    })

    // Query 2: Most Active Stocks (Proxy for Gainers/Losers section for now)
    const { data: activeStocks, isLoading: loadingActive } = useQuery({
        queryKey: ['active-volume'],
        queryFn: async () => {
            const res = await api.get('/market/activity/volume')
            return res.data.data as StockActivity[]
        }
    })

    return (
        <div className="space-y-8">
            {/* Header Section */}
            <div>
                <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">Market Pulse</h2>
                <p className="text-slate-600 dark:text-slate-400 mt-2">Live market overview and institutional activity.</p>
            </div>

            {/* Indices Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {loadingIndices ? (
                    [1, 2, 3, 4].map(i => (
                        <Card key={i} className="bg-slate-100 dark:bg-slate-900 border-slate-300 dark:border-slate-800 animate-pulse h-32" />
                    ))
                ) : indices?.map((item) => (
                    <Card key={item.name} className="bg-white dark:bg-slate-900/50 border-slate-300 dark:border-slate-800 backdrop-blur hover:bg-slate-100 dark:hover:bg-slate-900 transition cursor-default">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                                {item.name}
                            </CardTitle>
                            {item.is_up ? (
                                <TrendingUp className="h-4 w-4 text-emerald-500" />
                            ) : (
                                <Activity className="h-4 w-4 text-rose-500" />
                            )}
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white">
                                {item.value?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </div>
                            <p className={cn("text-xs flex items-center mt-1", item.is_up ? "text-emerald-500" : "text-rose-500")}>
                                {item.is_up ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                                {item.change_percent ? Math.abs(item.change_percent).toFixed(2) : '0.00'}%
                                <span className="ml-2 text-slate-400 dark:text-slate-500">
                                    ({item.change ? (item.change > 0 ? "+" : "") + item.change.toFixed(2) : '0.00'})
                                </span>
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Market Movers Section */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 bg-white dark:bg-slate-900/50 border-slate-300 dark:border-slate-800">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white">Trend Leaders (Volume)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="relative w-full overflow-auto">
                            <table className="w-full caption-bottom text-sm text-left">
                                <thead className="[&_tr]:border-b [&_tr]:border-slate-800">
                                    <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                        <th className="h-12 px-4 align-middle font-medium text-slate-600 dark:text-slate-400">Symbol</th>
                                        <th className="h-12 px-4 align-middle font-medium text-slate-600 dark:text-slate-400 text-right">Price</th>
                                        <th className="h-12 px-4 align-middle font-medium text-slate-600 dark:text-slate-400 text-right">% Chg</th>
                                        <th className="h-12 px-4 align-middle font-medium text-slate-600 dark:text-slate-400 text-right">Volume</th>
                                    </tr>
                                </thead>
                                <tbody className="[&_tr:last-child]:border-0">
                                    {loadingActive ? (
                                        <tr><td colSpan={4} className="p-4 text-center text-slate-600 dark:text-slate-500">Loading market data...</td></tr>
                                    ) : activeStocks?.slice(0, 10).map((stock) => (
                                        <tr key={stock.symbol} className="border-b border-slate-200 dark:border-slate-800 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800/50">
                                            <td className="p-4 align-middle font-medium text-slate-900 dark:text-white">{stock.symbol}</td>
                                            <td className="p-4 align-middle text-right text-slate-700 dark:text-slate-200">₹{stock.lastPrice?.toLocaleString()}</td>
                                            <td className={cn("p-4 align-middle text-right font-medium", stock.pChange >= 0 ? "text-emerald-600 dark:text-emerald-500" : "text-rose-600 dark:text-rose-500")}>
                                                {stock.pChange > 0 ? "+" : ""}{stock.pChange?.toFixed(2)}%
                                            </td>
                                            <td className="p-4 align-middle text-right text-slate-600 dark:text-slate-400">{(stock.totalTradedVolume / 100000).toFixed(2)}L</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>

                {/* Market Breadth Widget */}
                <MarketBreadthWidget />
            </div>
        </div>
    )
}
