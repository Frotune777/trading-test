"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Search, ShieldAlert, ShieldCheck, TrendingUp, Users, Activity, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

interface InsiderTrade {
    person: string
    typeOfSecurity: string
    acquisitionMode: string
    date: string
    value: number
}

interface SentinelResponse {
    symbol: string
    sentinel_score: number
    bias: string
    signals: string[]
    metrics: {
        insider_buys: number
        net_insider_value: string
        bulk_deal_qty: number
        block_deal_qty: number
        short_selling_pct: number
    }
}

export default function InsiderPage() {
    const [lookupSymbol, setLookupSymbol] = useState("INDOSTAR")
    const [searchSymbol, setSearchSymbol] = useState("INDOSTAR")

    // 1. Symbol-specific Sentinel Signals
    const { data: sentinel, isLoading: loadingSentinel } = useQuery<SentinelResponse>({
        queryKey: ['sentinel', lookupSymbol],
        queryFn: async () => {
            const res = await api.get(`/insider/sentinel/${lookupSymbol}`)
            return res.data
        }
    })

    // 2. Global Insider Trades
    const { data: trades, isLoading: loadingTrades } = useQuery({
        queryKey: ['insider-trades'],
        queryFn: async () => {
            const res = await api.get('/insider/trades')
            return res.data.data as InsiderTrade[]
        }
    })

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchSymbol) setLookupSymbol(searchSymbol.toUpperCase())
    }

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Sentinel Intelligence</h2>
                    <p className="text-slate-400 mt-2">Tracking institutional footprints and promoter conviction.</p>
                </div>
                
                <form onSubmit={handleSearch} className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input 
                            value={searchSymbol}
                            onChange={(e) => setSearchSymbol(e.target.value)}
                            placeholder="Search Symbol (e.g. RELIANCE)" 
                            className="bg-slate-900 border-slate-700 pl-10 w-64 text-white focus:ring-emerald-500/20"
                        />
                    </div>
                    <Button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white">Analyze</Button>
                </form>
            </div>

            {/* Top Row: Sentinel Insight + Market Stats */}
            <div className="grid gap-6 md:grid-cols-3 lg:grid-cols-4">
                {/* Sentinel Pillar Card */}
                <Card className="md:col-span-2 lg:col-span-2 bg-slate-900/40 border-slate-800 backdrop-blur-sm overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <ShieldCheck className="h-24 w-24" />
                    </div>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-white flex items-center gap-2">
                                    {sentinel?.bias === "BULLISH" ? <ShieldCheck className="h-5 w-5 text-emerald-500" /> : <ShieldAlert className="h-5 w-5 text-rose-500" />}
                                    {lookupSymbol} SENTINEL
                                </CardTitle>
                                <CardDescription className="text-slate-500">30-day institutional tracking</CardDescription>
                            </div>
                            <div className="text-right">
                                <div className={cn(
                                    "text-3xl font-black",
                                    sentinel?.bias === "BULLISH" ? "text-emerald-500" : (sentinel?.bias === "BEARISH" ? "text-rose-500" : "text-slate-400")
                                )}>
                                    {sentinel?.sentinel_score.toFixed(0)}
                                </div>
                                <div className="text-[10px] uppercase font-bold text-slate-500">Conviction</div>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex flex-wrap gap-2">
                                {sentinel?.signals.map((sig, i) => (
                                    <Badge key={i} variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-2 py-0.5 animate-pulse">
                                        {sig}
                                    </Badge>
                                ))}
                                {(!sentinel?.signals || sentinel.signals[0] === "None") && (
                                    <Badge variant="outline" className="bg-slate-500/10 text-slate-400 border-slate-500/20">
                                        No High-Conviction Patterns
                                    </Badge>
                                )}
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 mt-4">
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800/50">
                                    <div className="text-xs text-slate-500 mb-1 flex items-center gap-1"><Users className="h-3 w-3" /> Insider Buys</div>
                                    <div className="text-lg font-bold text-white">{sentinel?.metrics.insider_buys || 0}</div>
                                </div>
                                <div className="p-3 bg-slate-950/50 rounded-lg border border-slate-800/50">
                                    <div className="text-xs text-slate-500 mb-1 flex items-center gap-1"><TrendingUp className="h-3 w-3" /> Net Buy Value</div>
                                    <div className="text-lg font-bold text-emerald-500">{sentinel?.metrics.net_insider_value || "0"}</div>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Additional Stats */}
                <Card className="bg-slate-900/40 border-slate-800 flex flex-col justify-center p-6">
                    <div className="space-y-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-blue-500/10 rounded-full">
                                <BarChart3 className="h-6 w-6 text-blue-500" />
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase tracking-wider">Bulk Net Qty</div>
                                <div className={cn("text-xl font-bold", (sentinel?.metrics.bulk_deal_qty || 0) >= 0 ? "text-white" : "text-rose-500")}>
                                    {(sentinel?.metrics.bulk_deal_qty || 0).toLocaleString()}
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-purple-500/10 rounded-full">
                                <Activity className="h-6 w-6 text-purple-500" />
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase tracking-wider">Shorting %</div>
                                <div className="text-xl font-bold text-white">{sentinel?.metrics.short_selling_pct?.toFixed(2) || "0.00"}%</div>
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Legend/Quality Card */}
                <Card className="bg-slate-900 border-slate-800 flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-4">
                        <ShieldCheck className="h-8 w-8 text-emerald-500" />
                    </div>
                    <h3 className="text-white font-bold">Sentinel Verified</h3>
                    <p className="text-xs text-slate-500 mt-2 px-2">Signals are derived from SEBI filings and historical exchange data.</p>
                </Card>
            </div>

            {/* Market Wide Deals Table */}
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-white">Recent Insider Activity</CardTitle>
                            <CardDescription className="text-slate-500">Live feed of corporate filings across NSE</CardDescription>
                        </div>
                        <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-none">LIVE FEED</Badge>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border border-slate-800 overflow-hidden">
                        <Table>
                            <TableHeader className="bg-slate-950/50">
                                <TableRow className="border-slate-800 hover:bg-transparent">
                                    <TableHead className="text-slate-400">Trading Person</TableHead>
                                    <TableHead className="text-slate-400">Security</TableHead>
                                    <TableHead className="text-slate-400">Mode</TableHead>
                                    <TableHead className="text-slate-400">Date</TableHead>
                                    <TableHead className="text-slate-400 text-right">Value (₹)</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loadingTrades ? (
                                    <TableRow><TableCell colSpan={5} className="text-center py-8 text-slate-500">Syncing with NSE filings...</TableCell></TableRow>
                                ) : trades?.slice(0, 15).map((trade, i) => (
                                    <TableRow key={i} className="border-slate-800 hover:bg-slate-800/30 transition-colors">
                                        <TableCell className="font-medium text-white">{trade.person}</TableCell>
                                        <TableCell className="text-slate-400">{trade.typeOfSecurity}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className={cn(
                                                "border-none",
                                                trade.acquisitionMode.includes("Market") ? "bg-blue-500/10 text-blue-400" : "bg-orange-500/10 text-orange-400"
                                            )}>
                                                {trade.acquisitionMode}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-slate-500 text-xs">{trade.date}</TableCell>
                                        <TableCell className="text-right font-mono text-emerald-500 font-bold">
                                            {trade.value?.toLocaleString('en-IN')}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
