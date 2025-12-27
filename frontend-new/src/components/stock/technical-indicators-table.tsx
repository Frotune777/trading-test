"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface TechnicalIndicator {
    name: string
    value: number
    signal?: 'bullish' | 'bearish' | 'neutral'
}

interface TechnicalIndicatorsTableProps {
    indicators: any
    stats: any
}

export function TechnicalIndicatorsTable({ indicators, stats }: TechnicalIndicatorsTableProps) {
    if (!indicators || indicators.length === 0) {
        return (
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground">Technical Indicators</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-muted-foreground text-center py-8">
                        No technical indicators available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Get latest indicator values
    const latest = indicators[indicators.length - 1] || {}

    // Helper function to determine signal
    const getSignal = (name: string, value: number): 'bullish' | 'bearish' | 'neutral' => {
        if (name === 'RSI') {
            if (value > 70) return 'bearish' // Overbought
            if (value < 30) return 'bullish' // Oversold
            return 'neutral'
        }
        if (name.includes('MACD')) {
            return value > 0 ? 'bullish' : 'bearish'
        }
        return 'neutral'
    }

    // Prepare indicator list
    const indicatorList: TechnicalIndicator[] = [
        { name: 'RSI (14)', value: latest.RSI, signal: getSignal('RSI', latest.RSI) },
        { name: 'MACD', value: latest.MACD, signal: getSignal('MACD', latest.MACD) },
        { name: 'MACD Signal', value: latest.MACD_signal },
        { name: 'MACD Histogram', value: latest.MACD_histogram },
        { name: 'SMA (20)', value: latest.SMA_20 },
        { name: 'SMA (50)', value: latest.SMA_50 },
        { name: 'SMA (200)', value: latest.SMA_200 },
        { name: 'EMA (12)', value: latest.EMA_12 },
        { name: 'EMA (26)', value: latest.EMA_26 },
        { name: 'Bollinger Upper', value: latest.BB_upper },
        { name: 'Bollinger Middle', value: latest.BB_middle },
        { name: 'Bollinger Lower', value: latest.BB_lower },
        { name: 'ATR (14)', value: latest.ATR },
        { name: 'ADX', value: latest.ADX },
        { name: 'Stochastic %K', value: latest.STOCH_k },
        { name: 'Stochastic %D', value: latest.STOCH_d },
    ].filter(ind => ind.value !== undefined && ind.value !== null && !isNaN(ind.value))

    const SignalBadge = ({ signal }: { signal?: string }) => {
        if (!signal || signal === 'neutral') {
            return <Badge variant="outline" className="bg-muted text-muted-foreground border-border"><Minus className="h-3 w-3 mr-1" />Neutral</Badge>
        }
        if (signal === 'bullish') {
            return <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/30"><TrendingUp className="h-3 w-3 mr-1" />Bullish</Badge>
        }
        return <Badge variant="outline" className="bg-rose-500/10 text-rose-500 border-rose-500/30"><TrendingDown className="h-3 w-3 mr-1" />Bearish</Badge>
    }

    return (
        <Card className="bg-card border-border">
            <CardHeader>
                <CardTitle className="text-foreground">Technical Indicators</CardTitle>
                {stats && (
                    <div className="text-sm text-muted-foreground mt-2">
                        Volatility: {stats.volatility?.toFixed(2)}% | Avg Volume: {(stats.avg_volume / 100000).toFixed(2)}L
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <div className="grid gap-3 md:grid-cols-2">
                    {indicatorList.map((indicator, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border">
                            <div>
                                <div className="text-sm font-medium text-foreground">{indicator.name}</div>
                                <div className="text-xs text-muted-foreground mt-1">
                                    {indicator.value.toFixed(2)}
                                </div>
                            </div>
                            {indicator.signal && <SignalBadge signal={indicator.signal} />}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
