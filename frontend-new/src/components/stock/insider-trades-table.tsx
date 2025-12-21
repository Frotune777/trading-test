"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface InsiderTrade {
    symbol: string
    company: string
    person: string
    category: string
    typeOfSecurity: string
    acquisitionMode: string
    beforeAcqShares: number
    afterAcqShares: number
    noOfSecurities: number
    value: number
    date: string
}

interface InsiderTradesTableProps {
    data: InsiderTrade[] | null
    symbol?: string
}

export function InsiderTradesTable({ data, symbol }: InsiderTradesTableProps) {
    if (!data || data.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Insider Trades</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No insider trading data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Filter by symbol if provided
    const filteredData = symbol
        ? data.filter(trade => trade.symbol === symbol)
        : data

    // Limit to recent 20 trades
    const displayData = filteredData.slice(0, 20)

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">
                    Insider Trades
                    {symbol && <span className="text-sm text-slate-400 ml-2">({symbol})</span>}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="border-b border-slate-700">
                            <tr>
                                <th className="text-left p-3 text-slate-400 font-medium">Date</th>
                                <th className="text-left p-3 text-slate-400 font-medium">Person</th>
                                <th className="text-left p-3 text-slate-400 font-medium">Category</th>
                                <th className="text-left p-3 text-slate-400 font-medium">Type</th>
                                <th className="text-right p-3 text-slate-400 font-medium">Quantity</th>
                                <th className="text-right p-3 text-slate-400 font-medium">Value (₹)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayData.map((trade, index) => {
                                const isBuy = trade.acquisitionMode?.toLowerCase().includes('acquisition') ||
                                    trade.acquisitionMode?.toLowerCase().includes('purchase')
                                const isSell = trade.acquisitionMode?.toLowerCase().includes('sale') ||
                                    trade.acquisitionMode?.toLowerCase().includes('disposal')

                                return (
                                    <tr
                                        key={index}
                                        className="border-b border-slate-800 hover:bg-slate-800/30"
                                    >
                                        <td className="p-3 text-slate-300">
                                            {new Date(trade.date).toLocaleDateString('en-US', {
                                                month: 'short',
                                                day: 'numeric',
                                                year: 'numeric'
                                            })}
                                        </td>
                                        <td className="p-3 text-white max-w-[200px] truncate">
                                            {trade.person}
                                        </td>
                                        <td className="p-3">
                                            <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-700 text-xs">
                                                {trade.category}
                                            </Badge>
                                        </td>
                                        <td className="p-3">
                                            {isBuy && (
                                                <Badge variant="outline" className="bg-emerald-900/30 text-emerald-500 border-emerald-700 text-xs">
                                                    <TrendingUp className="h-3 w-3 mr-1" />
                                                    Buy
                                                </Badge>
                                            )}
                                            {isSell && (
                                                <Badge variant="outline" className="bg-rose-900/30 text-rose-500 border-rose-700 text-xs">
                                                    <TrendingDown className="h-3 w-3 mr-1" />
                                                    Sell
                                                </Badge>
                                            )}
                                            {!isBuy && !isSell && (
                                                <Badge variant="outline" className="bg-slate-800 text-slate-400 border-slate-700 text-xs">
                                                    Other
                                                </Badge>
                                            )}
                                        </td>
                                        <td className={cn(
                                            "p-3 text-right font-medium",
                                            isBuy && "text-emerald-500",
                                            isSell && "text-rose-500",
                                            !isBuy && !isSell && "text-slate-300"
                                        )}>
                                            {trade.noOfSecurities?.toLocaleString() || '-'}
                                        </td>
                                        <td className="p-3 text-right text-slate-300">
                                            {trade.value ? `₹${(trade.value / 100000).toFixed(2)}L` : '-'}
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    )
}
