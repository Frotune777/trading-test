"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Activity, BarChart3, DollarSign, Calendar, Loader2, Shield, TrendingUp, Clock } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { useMarketStatus } from "@/hooks/useMarketStatus"
import { calculateTechnicalSignal, getSignalDescription } from "@/lib/signal-utils"
import { TechnicalSignalMeter } from "@/components/analysis/TechnicalSignalMeter"
import { QUADAnalysisTab } from "@/components/analysis/QUADAnalysisTab"
import { TechnicalInsights } from "@/components/analysis/TechnicalInsights"
import { CorporateEvents } from "@/components/analysis/CorporateEvents"

interface TechnicalIndicator {
    [key: string]: number | string
}

interface TechnicalStats {
    volatility: number
    avg_volume: number
    price_range: number
    trend_strength: number
}

interface FinancialQuarterly {
    date: string
    revenue: number
    profit: number
    eps: number
    [key: string]: any
}

export default function AnalysisPage() {
    const { refreshInterval } = useMarketStatus()
    const [symbol, setSymbol] = useState("RELIANCE")
    const [searchInput, setSearchInput] = useState("RELIANCE")
    const [timeframe, setTimeframe] = useState("1d")
    const [activeTab, setActiveTab] = useState("quad")

    // Fetch Technical Indicators
    const { data: technicalData, isLoading: loadingTechnical, isFetching: fetchingTechnical, refetch: refetchTechnical, isError: errorTechnical } = useQuery({
        queryKey: ['technical-indicators', symbol],
        queryFn: async () => {
            const res = await api.get(`/technicals/indicators/${symbol}`)
            return res.data as { symbol: string; stats: TechnicalStats; indicators: TechnicalIndicator[] }
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market'),
        retry: 1, // Minimize retries to reset button faster on fail
        meta: { errorMessage: `Failed to load technicals for ${symbol}` }
    })

    // Fetch QUAD Reasoning
    const { data: quadData, isLoading: loadingQuad, isFetching: fetchingQuad, refetch: refetchQuad, isError: errorQuad } = useQuery({
        queryKey: ['quad-reasoning', symbol],
        queryFn: async () => {
            const res = await api.get(`/recommendations/${symbol}/reasoning`)
            return res.data
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market'),
        retry: 1
    })

    // Fetch Fundamental Data
    const { data: fundamentalData, isLoading: loadingFundamental, isFetching: fetchingFundamental, refetch: refetchFundamental, isError: errorFundamental } = useQuery({
        queryKey: ['stock-financials', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}/financials`)
            return res.data as { symbol: string; quarterly: FinancialQuarterly[]; annual: FinancialQuarterly[] }
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market'),
        retry: 1
    })

    const isAnyLoading = loadingTechnical || loadingQuad || loadingFundamental
    const isAnyFetching = (fetchingTechnical && !errorTechnical) || (fetchingQuad && !errorQuad) || (fetchingFundamental && !errorFundamental)

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (!searchInput) return

        const newSymbol = searchInput.toUpperCase()
        if (newSymbol === symbol) {
            // Force refresh if same symbol
            refetchTechnical()
            refetchQuad()
            refetchFundamental()
        } else {
            setSymbol(newSymbol)
        }
    }

    const latestIndicators = technicalData?.indicators?.[technicalData.indicators.length - 1]
    const stats = technicalData?.stats

    // Calculate aggregated signal
    const technicalSignal = latestIndicators ? calculateTechnicalSignal(latestIndicators) : null

    return (
        <div className="space-y-6">
            {/* Header with Search */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                        Stock Intelligence
                    </h2>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">
                        AI-powered analysis combining technical, fundamental, and market intelligence.
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <Input
                            type="text"
                            placeholder="Enter symbol (e.g., RELIANCE)"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
                            className="bg-white dark:bg-slate-900/50 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 w-48"
                        />
                        <Select value={timeframe} onValueChange={setTimeframe}>
                            <SelectTrigger className="w-28 bg-white dark:bg-slate-900/50 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white">
                                <Clock className="h-4 w-4 mr-2" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700">
                                <SelectItem value="1d" className="text-slate-900 dark:text-white">Daily</SelectItem>
                                <SelectItem value="1w" className="text-slate-900 dark:text-white">Weekly</SelectItem>
                                <SelectItem value="1h" className="text-slate-900 dark:text-white">Hourly</SelectItem>
                                <SelectItem value="15m" className="text-slate-900 dark:text-white">15 Min</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button
                            type="submit"
                            className="bg-blue-600 hover:bg-blue-700"
                            disabled={isAnyLoading || isAnyFetching}
                            data-testid="analyze-button"
                        >
                            {isAnyFetching ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Analyzing
                                </>
                            ) : (
                                "Analyze"
                            )}
                        </Button>
                    </form>
                </div>
            </div>

            {/* Quick Stats */}
            {stats && (
                <div className="grid gap-4 md:grid-cols-4">
                    <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 border-l-4 border-l-blue-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-600 dark:text-slate-500 uppercase tracking-wider">
                                Volatility
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white">{stats.volatility?.toFixed(2)}%</div>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1 flex items-center gap-1">
                                <Activity className="h-3 w-3" /> Price fluctuation
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 border-l-4 border-l-emerald-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-600 dark:text-slate-500 uppercase tracking-wider">
                                Avg Volume
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white">
                                {stats.avg_volume ? (stats.avg_volume / 1000000).toFixed(2) + 'M' : 'N/A'}
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1 flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" /> Trading liquidity
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 border-l-4 border-l-purple-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-600 dark:text-slate-500 uppercase tracking-wider">
                                Price Range
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white">₹{stats.price_range?.toFixed(2)}</div>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1 flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" /> High-Low spread
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 border-l-4 border-l-orange-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-600 dark:text-slate-500 uppercase tracking-wider">
                                Trend Strength
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white">{stats.trend_strength?.toFixed(0)}</div>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1 flex items-center gap-1">
                                <Activity className="h-3 w-3" /> Momentum
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                    <TabsTrigger value="quad" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        QUAD Analysis
                    </TabsTrigger>
                    <TabsTrigger value="signals" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white flex items-center gap-2">
                        <Activity className="h-4 w-4" />
                        Technical Signals
                    </TabsTrigger>
                    <TabsTrigger value="fundamental" className="data-[state=active]:bg-emerald-600 data-[state=active]:text-white flex items-center gap-2">
                        <DollarSign className="h-4 w-4" />
                        Fundamentals
                    </TabsTrigger>
                    <TabsTrigger value="indicators" className="data-[state=active]:bg-slate-600 data-[state=active]:text-white flex items-center gap-2">
                        <BarChart3 className="h-4 w-4" />
                        Technical Insights
                    </TabsTrigger>
                    <TabsTrigger value="events" className="data-[state=active]:bg-cyan-600 data-[state=active]:text-white flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        Corporate Events
                    </TabsTrigger>
                </TabsList>

                {/* QUAD Analysis Tab */}
                <TabsContent value="quad" className="mt-4">
                    <QUADAnalysisTab data={quadData} isLoading={loadingQuad} />
                </TabsContent>

                {/* Technical Signals Tab */}
                <TabsContent value="signals" className="mt-4">
                    {technicalSignal ? (
                        <TechnicalSignalMeter signal={technicalSignal} />
                    ) : (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
                            <span className="ml-3 text-slate-600 dark:text-slate-400">Calculating signals...</span>
                        </div>
                    )}
                </TabsContent>

                {/* Fundamental Tab */}
                <TabsContent value="fundamental" className="space-y-4 mt-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        {/* Quarterly Results */}
                        <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
                            <CardHeader>
                                <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                                    <Calendar className="h-5 w-5 text-blue-500" />
                                    Quarterly Results
                                </CardTitle>
                                <CardDescription>Latest quarterly financial performance</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {loadingFundamental ? (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                                    </div>
                                ) : fundamentalData?.quarterly && fundamentalData.quarterly.length > 0 ? (
                                    <div className="space-y-3">
                                        {fundamentalData.quarterly.slice(0, 4).map((q, idx) => (
                                            <div key={idx} className="p-3 bg-slate-950/50 rounded-lg border border-slate-800/50">
                                                <div className="text-xs text-slate-500 mb-2">{q.date}</div>
                                                <div className="grid grid-cols-3 gap-2 text-sm">
                                                    <div>
                                                        <div className="text-slate-500 text-xs">Revenue</div>
                                                        <div className="text-white font-medium">
                                                            {q.revenue ? `₹${(q.revenue / 10000000).toFixed(2)}Cr` : 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-500 text-xs">Profit</div>
                                                        <div className="text-emerald-500 font-medium">
                                                            {q.profit ? `₹${(q.profit / 10000000).toFixed(2)}Cr` : 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-500 text-xs">EPS</div>
                                                        <div className="text-white font-medium">
                                                            {q.eps ? `₹${q.eps.toFixed(2)}` : 'N/A'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-slate-600 dark:text-slate-500">
                                        No quarterly data available
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Annual Results */}
                        <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
                            <CardHeader>
                                <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                                    <DollarSign className="h-5 w-5 text-emerald-500" />
                                    Annual Results
                                </CardTitle>
                                <CardDescription>Yearly financial performance trends</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {loadingFundamental ? (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
                                    </div>
                                ) : fundamentalData?.annual && fundamentalData.annual.length > 0 ? (
                                    <div className="space-y-3">
                                        {fundamentalData.annual.slice(0, 4).map((a, idx) => (
                                            <div key={idx} className="p-3 bg-slate-950/50 rounded-lg border border-slate-800/50">
                                                <div className="text-xs text-slate-500 mb-2">{a.date}</div>
                                                <div className="grid grid-cols-3 gap-2 text-sm">
                                                    <div>
                                                        <div className="text-slate-500 text-xs">Revenue</div>
                                                        <div className="text-white font-medium">
                                                            {a.revenue ? `₹${(a.revenue / 10000000).toFixed(2)}Cr` : 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-500 text-xs">Profit</div>
                                                        <div className="text-emerald-500 font-medium">
                                                            {a.profit ? `₹${(a.profit / 10000000).toFixed(2)}Cr` : 'N/A'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-500 text-xs">EPS</div>
                                                        <div className="text-white font-medium">
                                                            {a.eps ? `₹${a.eps.toFixed(2)}` : 'N/A'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-slate-600 dark:text-slate-500">
                                        No annual data available
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* Technical Insights Tab - Replaces Raw Indicators */}
                <TabsContent value="indicators" className="mt-4">
                    <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-slate-900 dark:text-white">Technical Insights</CardTitle>
                            <CardDescription>Intelligent interpretation of technical indicators for {symbol}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loadingTechnical ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                                    <span className="ml-3 text-slate-600 dark:text-slate-400">Loading insights...</span>
                                </div>
                            ) : latestIndicators ? (
                                <TechnicalInsights indicators={latestIndicators} />
                            ) : (
                                <div className="text-center py-12 text-slate-600 dark:text-slate-500">
                                    No technical data available for this symbol
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Corporate Events Tab */}
                <TabsContent value="events" className="mt-4">
                    <CorporateEvents symbol={symbol} />
                </TabsContent>
            </Tabs>
        </div>
    )
}
