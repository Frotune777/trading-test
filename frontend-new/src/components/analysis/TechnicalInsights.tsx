import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Minus, Activity, AlertTriangle, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface TechnicalIndicator {
    [key: string]: number | string
}

interface TechnicalInsightsProps {
    indicators: TechnicalIndicator
}

export function TechnicalInsights({ indicators }: TechnicalInsightsProps) {
    if (!indicators) return null

    const close = Number(indicators.close)
    const sma20 = Number(indicators.sma_20)
    const sma50 = Number(indicators.sma_50)
    const sma200 = Number(indicators.sma_200)
    const rsi = Number(indicators.rsi)
    const macd = Number(indicators.macd)
    const macdSignal = Number(indicators.macd_signal)
    const adx = Number(indicators.adx)
    const atr = Number(indicators.atr)
    const bbUpper = Number(indicators.bb_upper)
    const bbLower = Number(indicators.bb_lower)
    const aroonUp = Number(indicators.aroon_up)
    const aroonDown = Number(indicators.aroon_down)

    // Trend Analysis
    const getTrendAnalysis = () => {
        const aboveSMA20 = close > sma20
        const aboveSMA50 = close > sma50
        const aboveSMA200 = close > sma200
        const smaAlignment = sma20 > sma50 && sma50 > sma200

        if (aboveSMA20 && aboveSMA50 && aboveSMA200 && smaAlignment) {
            return { trend: "Strong Uptrend", color: "emerald", icon: TrendingUp, strength: 5 }
        } else if (aboveSMA20 && aboveSMA50) {
            return { trend: "Uptrend", color: "green", icon: TrendingUp, strength: 4 }
        } else if (!aboveSMA20 && !aboveSMA50 && !aboveSMA200) {
            return { trend: "Strong Downtrend", color: "red", icon: TrendingDown, strength: 1 }
        } else if (!aboveSMA20 && !aboveSMA50) {
            return { trend: "Downtrend", color: "orange", icon: TrendingDown, strength: 2 }
        } else {
            return { trend: "Sideways", color: "slate", icon: Minus, strength: 3 }
        }
    }

    // Momentum Analysis
    const getMomentumAnalysis = () => {
        const macdBullish = macd > macdSignal
        const rsiOverbought = rsi > 70
        const rsiOversold = rsi < 30
        const rsiNeutral = rsi >= 40 && rsi <= 60

        if (macdBullish && rsi > 50 && !rsiOverbought) {
            return { status: "Bullish Momentum", color: "emerald", signal: "BUY" }
        } else if (!macdBullish && rsi < 50 && !rsiOversold) {
            return { status: "Bearish Momentum", color: "red", signal: "SELL" }
        } else if (rsiOverbought) {
            return { status: "Overbought", color: "orange", signal: "CAUTION" }
        } else if (rsiOversold) {
            return { status: "Oversold", color: "blue", signal: "OPPORTUNITY" }
        } else {
            return { status: "Neutral", color: "slate", signal: "HOLD" }
        }
    }

    // Volatility Analysis
    const getVolatilityAnalysis = () => {
        const atrPercent = (atr / close) * 100
        const nearUpperBB = close > bbUpper * 0.98
        const nearLowerBB = close < bbLower * 1.02

        if (atrPercent > 3) {
            return { level: "High Volatility", color: "red", risk: "High", atrPercent }
        } else if (atrPercent > 1.5) {
            return { level: "Moderate Volatility", color: "yellow", risk: "Medium", atrPercent }
        } else {
            return { level: "Low Volatility", color: "green", risk: "Low", atrPercent }
        }
    }

    // Candlestick Patterns
    const getCandlestickPatterns = () => {
        const patterns = []

        if (indicators.cdlengulfing === -100) patterns.push({ name: "Bearish Engulfing", signal: "BEARISH", color: "red" })
        if (indicators.cdlengulfing === 100) patterns.push({ name: "Bullish Engulfing", signal: "BULLISH", color: "emerald" })
        if (indicators.cdlhammer === 100) patterns.push({ name: "Hammer", signal: "BULLISH", color: "emerald" })
        if (indicators.cdlshootingstar === -100) patterns.push({ name: "Shooting Star", signal: "BEARISH", color: "red" })
        if (indicators.cdldoji !== 0) patterns.push({ name: "Doji", signal: "INDECISION", color: "yellow" })
        if (indicators.cdlmorningstar === 100) patterns.push({ name: "Morning Star", signal: "BULLISH", color: "emerald" })
        if (indicators.cdleveningstar === -100) patterns.push({ name: "Evening Star", signal: "BEARISH", color: "red" })
        if (indicators.cdl3whitesoldiers === 100) patterns.push({ name: "Three White Soldiers", signal: "BULLISH", color: "emerald" })
        if (indicators.cdl3blackcrows === -100) patterns.push({ name: "Three Black Crows", signal: "BEARISH", color: "red" })

        return patterns
    }

    const trendAnalysis = getTrendAnalysis()
    const momentumAnalysis = getMomentumAnalysis()
    const volatilityAnalysis = getVolatilityAnalysis()
    const patterns = getCandlestickPatterns()

    return (
        <div className="space-y-6">
            {/* Trend Analysis Card */}
            <Card className="bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
                <CardHeader>
                    <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                        <trendAnalysis.icon className={cn("h-5 w-5", `text-${trendAnalysis.color}-500`)} />
                        Trend Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Current Trend</span>
                        <Badge className={cn(
                            "text-white",
                            trendAnalysis.color === "emerald" && "bg-emerald-600",
                            trendAnalysis.color === "green" && "bg-green-600",
                            trendAnalysis.color === "red" && "bg-red-600",
                            trendAnalysis.color === "orange" && "bg-orange-600",
                            trendAnalysis.color === "slate" && "bg-slate-600"
                        )}>
                            {trendAnalysis.trend}
                        </Badge>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-200 dark:border-slate-800">
                        <div className="text-center">
                            <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">Price vs SMA20</div>
                            <div className={cn("text-sm font-semibold", close > sma20 ? "text-emerald-500" : "text-red-500")}>
                                {close > sma20 ? "Above" : "Below"}
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">Price vs SMA50</div>
                            <div className={cn("text-sm font-semibold", close > sma50 ? "text-emerald-500" : "text-red-500")}>
                                {close > sma50 ? "Above" : "Below"}
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">Price vs SMA200</div>
                            <div className={cn("text-sm font-semibold", close > sma200 ? "text-emerald-500" : "text-red-500")}>
                                {close > sma200 ? "Above" : "Below"}
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
                        <div className="text-xs text-slate-500 dark:text-slate-500 mb-2">Trend Strength</div>
                        <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((level) => (
                                <div
                                    key={level}
                                    className={cn(
                                        "h-2 flex-1 rounded",
                                        level <= trendAnalysis.strength
                                            ? trendAnalysis.color === "emerald" || trendAnalysis.color === "green"
                                                ? "bg-emerald-500"
                                                : trendAnalysis.color === "red" || trendAnalysis.color === "orange"
                                                    ? "bg-red-500"
                                                    : "bg-slate-500"
                                            : "bg-slate-800"
                                    )}
                                />
                            ))}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Momentum & RSI Card */}
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                        <Activity className="h-5 w-5 text-purple-500" />
                        Momentum Indicators
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Status</span>
                        <Badge className={cn(
                            "text-white",
                            momentumAnalysis.color === "emerald" && "bg-emerald-600",
                            momentumAnalysis.color === "red" && "bg-red-600",
                            momentumAnalysis.color === "orange" && "bg-orange-600",
                            momentumAnalysis.color === "blue" && "bg-blue-600",
                            momentumAnalysis.color === "slate" && "bg-slate-600"
                        )}>
                            {momentumAnalysis.status}
                        </Badge>
                    </div>

                    <div className="space-y-3">
                        <div>
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-slate-600 dark:text-slate-400">RSI (14)</span>
                                <span className={cn(
                                    "font-semibold",
                                    rsi > 70 ? "text-red-500" : rsi < 30 ? "text-blue-500" : "text-slate-900 dark:text-slate-300"
                                )}>
                                    {rsi.toFixed(2)}
                                </span>
                            </div>
                            <div className="relative h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className={cn(
                                        "absolute h-full rounded-full transition-all",
                                        rsi > 70 ? "bg-red-500" : rsi < 30 ? "bg-blue-500" : "bg-emerald-500"
                                    )}
                                    style={{ width: `${rsi}%` }}
                                />
                                <div className="absolute left-[30%] top-0 h-full w-px bg-slate-400 dark:bg-slate-600" />
                                <div className="absolute left-[70%] top-0 h-full w-px bg-slate-400 dark:bg-slate-600" />
                            </div>
                            <div className="flex justify-between text-xs text-slate-500 mt-1">
                                <span>Oversold (30)</span>
                                <span>Overbought (70)</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-200 dark:border-slate-800">
                            <div>
                                <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">MACD</div>
                                <div className={cn("text-sm font-semibold", macd > macdSignal ? "text-emerald-500" : "text-red-500")}>
                                    {macd > macdSignal ? "Bullish" : "Bearish"}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">ADX (Trend Strength)</div>
                                <div className={cn("text-sm font-semibold", adx > 25 ? "text-emerald-500" : "text-slate-600 dark:text-slate-400")}>
                                    {adx.toFixed(1)} {adx > 25 ? "(Strong)" : "(Weak)"}
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Volatility Card */}
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                        <Activity className="h-5 w-5 text-yellow-500" />
                        Volatility Assessment
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-slate-600 dark:text-slate-400">Volatility Level</span>
                        <Badge className={cn(
                            "text-white",
                            volatilityAnalysis.color === "red" && "bg-red-600",
                            volatilityAnalysis.color === "yellow" && "bg-yellow-600",
                            volatilityAnalysis.color === "green" && "bg-green-600"
                        )}>
                            {volatilityAnalysis.level}
                        </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">ATR %</div>
                            <div className="text-lg font-semibold text-slate-900 dark:text-white">
                                {volatilityAnalysis.atrPercent.toFixed(2)}%
                            </div>
                        </div>
                        <div>
                            <div className="text-xs text-slate-500 dark:text-slate-500 mb-1">Risk Level</div>
                            <div className={cn(
                                "text-lg font-semibold",
                                volatilityAnalysis.risk === "High" && "text-red-500",
                                volatilityAnalysis.risk === "Medium" && "text-yellow-500",
                                volatilityAnalysis.risk === "Low" && "text-green-500"
                            )}>
                                {volatilityAnalysis.risk}
                            </div>
                        </div>
                    </div>

                    <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                        <div className="text-xs text-slate-500 dark:text-slate-500 mb-2">Bollinger Bands Position</div>
                        <div className="text-sm text-slate-700 dark:text-slate-300">
                            {close > bbUpper * 0.98 ? "Near Upper Band (Overbought)" :
                                close < bbLower * 1.02 ? "Near Lower Band (Oversold)" :
                                    "Within Bands (Normal)"}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Candlestick Patterns Card */}
            {patterns.length > 0 && (
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-orange-500" />
                            Detected Patterns
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {patterns.map((pattern, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-950/50 rounded-lg border border-slate-200 dark:border-slate-800">
                                    <span className="text-slate-900 dark:text-white font-medium">{pattern.name}</span>
                                    <Badge className={cn(
                                        "text-white",
                                        pattern.color === "emerald" && "bg-emerald-600",
                                        pattern.color === "red" && "bg-red-600",
                                        pattern.color === "yellow" && "bg-yellow-600"
                                    )}>
                                        {pattern.signal}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {patterns.length === 0 && (
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                            <CheckCircle2 className="h-5 w-5 text-slate-500" />
                            Candlestick Patterns
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-slate-600 dark:text-slate-400 text-sm">No significant candlestick patterns detected in the current timeframe.</p>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
