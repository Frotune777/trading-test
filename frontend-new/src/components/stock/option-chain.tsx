"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface OptionData {
    strikePrice: number
    expiryDate: string
    underlying: string
    identifier: string
    openInterest: number
    changeinOpenInterest: number
    pchangeinOpenInterest: number
    totalTradedVolume: number
    impliedVolatility: number
    lastPrice: number
    change: number
    pChange: number
    totalBuyQuantity: number
    totalSellQuantity: number
    bidQty: number
    bidprice: number
    askQty: number
    askPrice: number
    underlyingValue: number
}

interface OptionChainData {
    records: {
        expiryDates: string[]
        data: Array<{
            strikePrice: number
            expiryDate: string
            CE?: OptionData
            PE?: OptionData
        }>
        strikePrices: number[]
        underlyingValue: number
    }
}

interface OptionChainProps {
    data: OptionChainData | null
    symbol: string
}

export function OptionChain({ data, symbol }: OptionChainProps) {
    if (!data || !data.records || !data.records.data) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Option Chain</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No option chain data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    const { records } = data
    const underlyingValue = records.underlyingValue || 0

    // Find ATM strike
    const atmStrike = records.strikePrices?.reduce((prev, curr) =>
        Math.abs(curr - underlyingValue) < Math.abs(prev - underlyingValue) ? curr : prev
        , records.strikePrices[0])

    // Limit to strikes around ATM (±10 strikes)
    const atmIndex = records.data.findIndex(item => item.strikePrice === atmStrike)
    const startIndex = Math.max(0, atmIndex - 10)
    const endIndex = Math.min(records.data.length, atmIndex + 11)
    const displayData = records.data.slice(startIndex, endIndex)

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">
                    Option Chain - {symbol}
                    <span className="text-sm text-slate-400 ml-3">
                        Spot: ₹{underlyingValue.toLocaleString()}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="border-b border-slate-700">
                            <tr>
                                {/* Call Options */}
                                <th className="text-emerald-500 p-2 text-right">OI</th>
                                <th className="text-emerald-500 p-2 text-right">Vol</th>
                                <th className="text-emerald-500 p-2 text-right">LTP</th>
                                <th className="text-emerald-500 p-2 text-right">Chg%</th>
                                <th className="text-emerald-500 p-2 text-right">IV</th>

                                {/* Strike */}
                                <th className="text-white p-2 text-center bg-slate-800">Strike</th>

                                {/* Put Options */}
                                <th className="text-rose-500 p-2 text-left">IV</th>
                                <th className="text-rose-500 p-2 text-left">Chg%</th>
                                <th className="text-rose-500 p-2 text-left">LTP</th>
                                <th className="text-rose-500 p-2 text-left">Vol</th>
                                <th className="text-rose-500 p-2 text-left">OI</th>
                            </tr>
                        </thead>
                        <tbody>
                            {displayData.map((item, index) => {
                                const isATM = item.strikePrice === atmStrike
                                const isITM_CE = item.strikePrice < underlyingValue
                                const isITM_PE = item.strikePrice > underlyingValue

                                return (
                                    <tr
                                        key={index}
                                        className={cn(
                                            "border-b border-slate-800 hover:bg-slate-800/30",
                                            isATM && "bg-blue-900/20"
                                        )}
                                    >
                                        {/* Call Data */}
                                        <td className={cn("p-2 text-right", isITM_CE && "bg-emerald-900/10")}>
                                            {item.CE ? (item.CE.openInterest / 1000).toFixed(0) + 'K' : '-'}
                                        </td>
                                        <td className={cn("p-2 text-right", isITM_CE && "bg-emerald-900/10")}>
                                            {item.CE ? (item.CE.totalTradedVolume / 1000).toFixed(0) + 'K' : '-'}
                                        </td>
                                        <td className={cn("p-2 text-right font-medium text-white", isITM_CE && "bg-emerald-900/10")}>
                                            {item.CE ? '₹' + item.CE.lastPrice.toFixed(2) : '-'}
                                        </td>
                                        <td className={cn(
                                            "p-2 text-right",
                                            isITM_CE && "bg-emerald-900/10",
                                            item.CE && item.CE.pChange > 0 ? "text-emerald-500" : "text-rose-500"
                                        )}>
                                            {item.CE ? item.CE.pChange.toFixed(2) + '%' : '-'}
                                        </td>
                                        <td className={cn("p-2 text-right text-slate-400", isITM_CE && "bg-emerald-900/10")}>
                                            {item.CE ? item.CE.impliedVolatility.toFixed(2) + '%' : '-'}
                                        </td>

                                        {/* Strike Price */}
                                        <td className={cn(
                                            "p-2 text-center font-bold bg-slate-800",
                                            isATM && "text-blue-400"
                                        )}>
                                            {item.strikePrice}
                                        </td>

                                        {/* Put Data */}
                                        <td className={cn("p-2 text-left text-slate-400", isITM_PE && "bg-rose-900/10")}>
                                            {item.PE ? item.PE.impliedVolatility.toFixed(2) + '%' : '-'}
                                        </td>
                                        <td className={cn(
                                            "p-2 text-left",
                                            isITM_PE && "bg-rose-900/10",
                                            item.PE && item.PE.pChange > 0 ? "text-emerald-500" : "text-rose-500"
                                        )}>
                                            {item.PE ? item.PE.pChange.toFixed(2) + '%' : '-'}
                                        </td>
                                        <td className={cn("p-2 text-left font-medium text-white", isITM_PE && "bg-rose-900/10")}>
                                            {item.PE ? '₹' + item.PE.lastPrice.toFixed(2) : '-'}
                                        </td>
                                        <td className={cn("p-2 text-left", isITM_PE && "bg-rose-900/10")}>
                                            {item.PE ? (item.PE.totalTradedVolume / 1000).toFixed(0) + 'K' : '-'}
                                        </td>
                                        <td className={cn("p-2 text-left", isITM_PE && "bg-rose-900/10")}>
                                            {item.PE ? (item.PE.openInterest / 1000).toFixed(0) + 'K' : '-'}
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
                <div className="mt-4 text-xs text-slate-500 flex gap-4">
                    <span className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-blue-900/20 border border-blue-700"></div>
                        ATM Strike
                    </span>
                    <span className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-emerald-900/10"></div>
                        ITM Calls
                    </span>
                    <span className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-rose-900/10"></div>
                        ITM Puts
                    </span>
                </div>
            </CardContent>
        </Card>
    )
}
