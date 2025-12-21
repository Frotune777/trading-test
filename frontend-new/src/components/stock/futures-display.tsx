"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowUpRight, ArrowDownRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface FuturesData {
    symbol: string
    expiryDate: string
    lastPrice: number
    change: number
    pChange: number
    openInterest: number
    changeinOpenInterest: number
    underlyingValue: number
}

interface FuturesDisplayProps {
    data: FuturesData[] | null
    symbol: string
}

export function FuturesDisplay({ data, symbol }: FuturesDisplayProps) {
    if (!data || data.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Futures Data</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No futures data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Get near month contract (first one)
    const nearMonth = data[0]
    const basis = nearMonth.lastPrice - nearMonth.underlyingValue
    const basisPercent = (basis / nearMonth.underlyingValue) * 100

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">Futures - {symbol}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Near Month Contract */}
                    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                        <div className="text-xs text-slate-400 mb-3">
                            Near Month: {new Date(nearMonth.expiryDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-sm text-slate-400">Futures Price</div>
                                <div className="text-2xl font-bold text-white mt-1">
                                    ₹{nearMonth.lastPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                                <div className={cn(
                                    "flex items-center text-sm mt-1",
                                    nearMonth.pChange >= 0 ? "text-emerald-500" : "text-rose-500"
                                )}>
                                    {nearMonth.pChange >= 0 ? <ArrowUpRight className="h-4 w-4 mr-1" /> : <ArrowDownRight className="h-4 w-4 mr-1" />}
                                    {nearMonth.change.toFixed(2)} ({nearMonth.pChange.toFixed(2)}%)
                                </div>
                            </div>

                            <div>
                                <div className="text-sm text-slate-400">Spot Price</div>
                                <div className="text-2xl font-bold text-white mt-1">
                                    ₹{nearMonth.underlyingValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Basis Analysis */}
                    <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-xs text-slate-400">Basis</div>
                            <div className={cn(
                                "text-lg font-bold mt-1",
                                basis >= 0 ? "text-emerald-500" : "text-rose-500"
                            )}>
                                ₹{basis.toFixed(2)}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {basisPercent.toFixed(2)}%
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-xs text-slate-400">Open Interest</div>
                            <div className="text-lg font-bold text-white mt-1">
                                {(nearMonth.openInterest / 1000000).toFixed(2)}M
                            </div>
                            <div className={cn(
                                "text-xs mt-1",
                                nearMonth.changeinOpenInterest >= 0 ? "text-emerald-500" : "text-rose-500"
                            )}>
                                {nearMonth.changeinOpenInterest >= 0 ? '+' : ''}{(nearMonth.changeinOpenInterest / 1000).toFixed(0)}K
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-xs text-slate-400">Cost of Carry</div>
                            <div className={cn(
                                "text-lg font-bold mt-1",
                                basis >= 0 ? "text-emerald-500" : "text-rose-500"
                            )}>
                                {basis >= 0 ? 'Contango' : 'Backwardation'}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {Math.abs(basisPercent).toFixed(2)}%
                            </div>
                        </div>
                    </div>

                    {/* All Contracts */}
                    {data.length > 1 && (
                        <div>
                            <div className="text-sm font-medium text-white mb-2">All Contracts</div>
                            <div className="space-y-2">
                                {data.map((contract, index) => (
                                    <div key={index} className="flex items-center justify-between text-sm p-2 bg-slate-800/30 rounded border border-slate-700">
                                        <span className="text-slate-400">
                                            {new Date(contract.expiryDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                        </span>
                                        <span className="text-white font-medium">
                                            ₹{contract.lastPrice.toFixed(2)}
                                        </span>
                                        <span className={cn(
                                            "font-medium",
                                            contract.pChange >= 0 ? "text-emerald-500" : "text-rose-500"
                                        )}>
                                            {contract.pChange >= 0 ? '+' : ''}{contract.pChange.toFixed(2)}%
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
