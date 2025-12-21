"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface BlockDeal {
    symbol: string
    clientName: string
    dealType: string
    quantity: number
    price: number
    date: string
}

interface BlockDealsTableProps {
    data: BlockDeal[] | null
    symbol?: string
}

export function BlockDealsTable({ data, symbol }: BlockDealsTableProps) {
    if (!data || data.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Block Deals</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No block deals data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Filter by symbol if provided
    const filteredData = symbol
        ? data.filter(deal => deal.symbol === symbol)
        : data

    // Limit to recent 15 deals
    const displayData = filteredData.slice(0, 15)

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">
                    Block Deals
                    {symbol && <span className="text-sm text-slate-400 ml-2">({symbol})</span>}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="border-b border-slate-700">
                            <tr>
                                <th className="text-left p-3 text-slate-400 font-medium">Date</th>
                                <th className="text-left p-3 text-slate-400 font-medium">Client Name</th>
                                <th className="text-left p-3 text-slate-400 font-medium">Deal Type</th>
                                <th className="text-right p-3 text-slate-400 font-medium">Quantity</th>
                                <th className="text-right p-3 text-slate-400 font-medium">Price (₹)</th>
                                <th className="text-right p-3 text-slate-400 font-medium">Value (₹)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayData.map((deal, index) => {
                                const isBuy = deal.dealType?.toLowerCase().includes('buy') ||
                                    deal.dealType?.toLowerCase().includes('purchase')
                                const totalValue = deal.quantity * deal.price

                                return (
                                    <tr
                                        key={index}
                                        className="border-b border-slate-800 hover:bg-slate-800/30"
                                    >
                                        <td className="p-3 text-slate-300">
                                            {new Date(deal.date).toLocaleDateString('en-US', {
                                                month: 'short',
                                                day: 'numeric',
                                                year: 'numeric'
                                            })}
                                        </td>
                                        <td className="p-3 text-white max-w-[250px] truncate">
                                            {deal.clientName}
                                        </td>
                                        <td className="p-3">
                                            <Badge
                                                variant="outline"
                                                className={cn(
                                                    "text-xs",
                                                    isBuy
                                                        ? "bg-emerald-900/30 text-emerald-500 border-emerald-700"
                                                        : "bg-rose-900/30 text-rose-500 border-rose-700"
                                                )}
                                            >
                                                {deal.dealType}
                                            </Badge>
                                        </td>
                                        <td className="p-3 text-right text-slate-300 font-medium">
                                            {deal.quantity?.toLocaleString()}
                                        </td>
                                        <td className="p-3 text-right text-slate-300">
                                            ₹{deal.price?.toFixed(2)}
                                        </td>
                                        <td className="p-3 text-right text-white font-medium">
                                            ₹{(totalValue / 100000).toFixed(2)}L
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
