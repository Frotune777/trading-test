"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown } from "lucide-react"

interface PCRData {
    symbol: string
    pcr: number
    total_call_oi: number
    total_put_oi: number
    interpretation: string
}

interface PCRChartProps {
    data: PCRData | null
    symbol: string
}

export function PCRChart({ data, symbol }: PCRChartProps) {
    if (!data) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Put-Call Ratio (PCR)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-slate-500 text-center py-8">
                        No PCR data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    const { pcr, total_call_oi, total_put_oi, interpretation } = data

    // Determine sentiment based on PCR
    const getSentiment = () => {
        if (pcr > 1.2) return { label: 'Bullish', color: 'text-emerald-500', icon: TrendingUp }
        if (pcr < 0.8) return { label: 'Bearish', color: 'text-rose-500', icon: TrendingDown }
        return { label: 'Neutral', color: 'text-slate-400', icon: TrendingUp }
    }

    const sentiment = getSentiment()
    const SentimentIcon = sentiment.icon

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">Put-Call Ratio (PCR)</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    {/* PCR Value */}
                    <div className="text-center">
                        <div className="text-5xl font-bold text-white mb-2">
                            {pcr.toFixed(2)}
                        </div>
                        <Badge
                            variant="outline"
                            className={cn(
                                "text-sm px-3 py-1",
                                sentiment.label === 'Bullish' && "bg-emerald-900/30 text-emerald-500 border-emerald-700",
                                sentiment.label === 'Bearish' && "bg-rose-900/30 text-rose-500 border-rose-700",
                                sentiment.label === 'Neutral' && "bg-slate-800 text-slate-400 border-slate-700"
                            )}
                        >
                            <SentimentIcon className="h-4 w-4 mr-1" />
                            {sentiment.label}
                        </Badge>
                    </div>

                    {/* OI Breakdown */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400">Total Put OI</span>
                            <span className="text-white font-medium">
                                {(total_put_oi / 1000000).toFixed(2)}M
                            </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2">
                            <div
                                className="bg-rose-500 h-2 rounded-full"
                                style={{ width: `${(total_put_oi / (total_put_oi + total_call_oi)) * 100}%` }}
                            />
                        </div>

                        <div className="flex justify-between items-center">
                            <span className="text-slate-400">Total Call OI</span>
                            <span className="text-white font-medium">
                                {(total_call_oi / 1000000).toFixed(2)}M
                            </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2">
                            <div
                                className="bg-emerald-500 h-2 rounded-full"
                                style={{ width: `${(total_call_oi / (total_put_oi + total_call_oi)) * 100}%` }}
                            />
                        </div>
                    </div>

                    {/* Interpretation */}
                    {interpretation && (
                        <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
                            <div className="text-xs text-slate-400 mb-1">Interpretation</div>
                            <div className="text-sm text-slate-200">{interpretation}</div>
                        </div>
                    )}

                    {/* Info */}
                    <div className="text-xs text-slate-500 text-center">
                        PCR = Put OI / Call OI. Higher values indicate bullish sentiment.
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function cn(...classes: any[]) {
    return classes.filter(Boolean).join(' ')
}
