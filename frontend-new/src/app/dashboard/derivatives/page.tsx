"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Search, Activity, Box, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface OptionChainItem {
    STRIKE_PRICE: number
    CALLS_Chng_in_OI: number
    CALLS_OI: number
    CALLS_Last_Price: number
    PUTS_Chng_in_OI: number
    PUTS_OI: number
    PUTS_Last_Price: number
}

export default function DerivativesPage() {
    const [symbol, setSymbol] = useState("NIFTY")
    const [searchVal, setSearchVal] = useState("NIFTY")

    const { data: oc, isLoading } = useQuery({
        queryKey: ['option-chain', symbol],
        queryFn: async () => {
            const res = await api.get(`/derivatives/option-chain/${symbol}`)
            return res.data.data as OptionChainItem[]
        }
    })

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchVal) setSymbol(searchVal.toUpperCase())
    }

    const totalCallsOI = oc?.reduce((acc, curr) => acc + (curr.CALLS_OI || 0), 0) || 0
    const totalPutsOI = oc?.reduce((acc, curr) => acc + (curr.PUTS_OI || 0), 0) || 0
    const pcr = totalCallsOI > 0 ? (totalPutsOI / totalCallsOI).toFixed(2) : "0.00"

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Derivatives Engine</h2>
                    <p className="text-slate-400 mt-2">Live Option Chain and Put-Call Ratio analysis.</p>
                </div>
                
                <form onSubmit={handleSearch} className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                        <Input 
                            value={searchVal}
                            onChange={(e) => setSearchVal(e.target.value)}
                            placeholder="Index or Stock (e.g. NIFTY)" 
                            className="bg-slate-900 border-slate-700 pl-10 w-64 text-white"
                        />
                    </div>
                    <Button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white">Fetch Chain</Button>
                </form>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-400">Put-Call Ratio (OI)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-white">{pcr}</div>
                        <p className={cn("text-xs mt-1", Number(pcr) > 1.2 ? "text-emerald-500" : (Number(pcr) < 0.7 ? "text-rose-500" : "text-slate-400"))}>
                            {Number(pcr) > 1.2 ? "Bullish Sentiment" : (Number(pcr) < 0.7 ? "Bearish Sentiment" : "Neutral / Side-ways")}
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-400">Total Calls OI</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-rose-500">{totalCallsOI.toLocaleString()}</div>
                    </CardContent>
                </Card>
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-400">Total Puts OI</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold text-emerald-500">{totalPutsOI.toLocaleString()}</div>
                    </CardContent>
                </Card>
            </div>

            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Option Chain: {symbol}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border border-slate-800">
                        <Table>
                            <TableHeader className="bg-slate-950/50">
                                <TableRow className="border-slate-800">
                                    <TableHead className="text-rose-500 font-bold text-center border-r border-slate-800">CALLS</TableHead>
                                    <TableHead className="text-slate-400 text-center">STRIKE</TableHead>
                                    <TableHead className="text-emerald-500 font-bold text-center border-l border-slate-800">PUTS</TableHead>
                                </TableRow>
                                <TableRow className="border-slate-800 text-[10px] uppercase text-slate-500">
                                    <TableHead className="text-center p-1 border-r border-slate-800">
                                        <div className="flex justify-around"><span>OI</span><span>Price</span><span>Chg%</span></div>
                                    </TableHead>
                                    <TableHead className="text-center p-1">-</TableHead>
                                    <TableHead className="text-center p-1 border-l border-slate-800">
                                        <div className="flex justify-around"><span>Chg%</span><span>Price</span><span>OI</span></div>
                                    </TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow><TableCell colSpan={3} className="text-center py-10">Loading Chain...</TableCell></TableRow>
                                ) : oc?.slice(0, 20).map((row, i) => (
                                    <TableRow key={i} className="border-slate-800 hover:bg-slate-800/20">
                                        <TableCell className="p-2 border-r border-slate-800">
                                            <div className="flex justify-around text-xs">
                                                <span className="text-slate-400">{row.CALLS_OI?.toLocaleString()}</span>
                                                <span className="text-white font-mono">₹{row.CALLS_Last_Price}</span>
                                                <span className={cn(row.CALLS_Chng_in_OI > 0 ? "text-emerald-500" : "text-rose-500")}>
                                                    {row.CALLS_Chng_in_OI > 0 ? "+" : ""}{row.CALLS_Chng_in_OI}
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="p-2 text-center font-bold text-blue-400 bg-blue-500/5">
                                            {row.STRIKE_PRICE}
                                        </TableCell>
                                        <TableCell className="p-2 border-l border-slate-800">
                                            <div className="flex justify-around text-xs">
                                                <span className={cn(row.PUTS_Chng_in_OI > 0 ? "text-emerald-500" : "text-rose-500")}>
                                                    {row.PUTS_Chng_in_OI > 0 ? "+" : ""}{row.PUTS_Chng_in_OI}
                                                </span>
                                                <span className="text-white font-mono">₹{row.PUTS_Last_Price}</span>
                                                <span className="text-slate-400">{row.PUTS_OI?.toLocaleString()}</span>
                                            </div>
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
