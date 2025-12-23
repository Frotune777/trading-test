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
import { Search, Activity, BarChart3, DollarSign, Calendar, Loader2, Shield, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { useMarketStatus } from "@/hooks/useMarketStatus"
import { calculateTechnicalSignal, getSignalDescription } from "@/lib/signal-utils"
import { TechnicalSignalMeter } from "@/components/analysis/TechnicalSignalMeter"
import { QUADAnalysisTab } from "@/components/analysis/QUADAnalysisTab"

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
    const [activeTab, setActiveTab] = useState("quad")

    // Fetch Technical Indicators
    const { data: technicalData, isLoading: loadingTechnical } = useQuery({
        queryKey: ['technical-indicators', symbol],
        queryFn: async () => {
            const res = await api.get(`/technicals/indicators/${symbol}`)
            return res.data as { symbol: string; stats: TechnicalStats; indicators: TechnicalIndicator[] }
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market')
    })

    // Fetch QUAD Reasoning
    const { data: quadData, isLoading: loadingQuad } = useQuery({
        queryKey: ['quad-reasoning', symbol],
        queryFn: async () => {
            const res = await api.get(`/recommendations/${symbol}/reasoning`)
            return res.data
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market')
    })

    // Fetch Fundamental Data
    const { data: fundamentalData, isLoading: loadingFundamental } = useQuery({
        queryKey: ['stock-financials', symbol],
        queryFn: async () => {
            const res = await api.get(`/stocks/${symbol}/financials`)
            return res.data as { symbol: string; quarterly: FinancialQuarterly[]; annual: FinancialQuarterly[] }
        },
        enabled: !!symbol,
        refetchInterval: refreshInterval('market')
    })

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchInput) setSymbol(searchInput.toUpperCase())
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
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                        Stock Intelligence
                    </h2>
                    <p className="text-slate-400 mt-2">AI-powered analysis combining technical, fundamental, and market intelligence.</p>
                </div>
                
                <form onSubmit={handleSearch} className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input 
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            placeholder="Enter symbol (e.g. RELIANCE)" 
                            className="bg-slate-900 border-slate-700 pl-10 w-64 text-white"
                        />
                    </div>
                    <Button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white">
                        Analyze
                    </Button>
                </form>
            </div>

            {/* Quick Stats */}
            {stats && (
                <div className="grid gap-4 md:grid-cols-4">
                    <Card className="bg-slate-900/50 border-slate-800 border-l-4 border-l-blue-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                Volatility
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stats.volatility?.toFixed(2)}%</div>
                            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <Activity className="h-3 w-3" /> Price fluctuation
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 border-l-4 border-l-emerald-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                Avg Volume
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">
                                {stats.avg_volume ? (stats.avg_volume / 1000000).toFixed(2) + 'M' : 'N/A'}
                            </div>
                            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" /> Trading liquidity
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 border-l-4 border-l-purple-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                Price Range
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">₹{stats.price_range?.toFixed(2)}</div>
                            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" /> High-Low spread
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="bg-slate-900/50 border-slate-800 border-l-4 border-l-orange-500">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                Trend Strength
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stats.trend_strength?.toFixed(0)}</div>
                            <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <Activity className="h-3 w-3" /> Momentum
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="bg-slate-900 border border-slate-800">
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
                        Raw Indicators
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
                            <span className="ml-3 text-slate-400">Calculating signals...</span>
                        </div>
                    )}
                </TabsContent>

                {/* Fundamental Tab */}
                <TabsContent value="fundamental" className="space-y-4 mt-4">
                    <div className="grid gap-6 md:grid-cols-2">
                        {/* Quarterly Results */}
                        <Card className="bg-slate-900/50 border-slate-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
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
                                    <div className="text-center py-8 text-slate-500">
                                        No quarterly data available
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Annual Results */}
                        <Card className="bg-slate-900/50 border-slate-800">
                            <CardHeader>
                                <CardTitle className="text-white flex items-center gap-2">
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
                                    <div className="text-center py-8 text-slate-500">
                                        No annual data available
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                {/* Raw Indicators Tab */}
                <TabsContent value="indicators" className="mt-4">
                    <Card className="bg-slate-900/50 border-slate-800">
                        <CardHeader>
                            <CardTitle className="text-white">All Technical Indicators</CardTitle>
                            <CardDescription>Comprehensive technical analysis metrics for {symbol}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loadingTechnical ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                                    <span className="ml-3 text-slate-400">Loading indicators...</span>
                                </div>
                            ) : latestIndicators ? (
                                <div className="rounded-md border border-slate-800 overflow-hidden">
                                    <Table>
                                        <TableHeader className="bg-slate-950/50">
                                            <TableRow className="border-slate-800">
                                                <TableHead className="text-slate-400">Indicator</TableHead>
                                                <TableHead className="text-slate-400 text-right">Value</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {Object.entries(latestIndicators)
                                                .filter(([key]) => !['Date', 'Timestamp', 'date', 'timestamp'].includes(key))
                                                .map(([key, value]) => (
                                                    <TableRow key={key} className="border-slate-800 hover:bg-slate-800/30">
                                                        <TableCell className="font-medium text-white">{key}</TableCell>
                                                        <TableCell className="text-right text-slate-300 font-mono">
                                                            {typeof value === 'number' ? value.toFixed(4) : value}
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            ) : (
                                <div className="text-center py-12 text-slate-500">
                                    No indicator data available for this symbol
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
