/**
 * Technical Signal Meter Component
 * 
 * Displays aggregated technical signal strength with visual indicators
 */

'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Activity, BarChart3, Volume2, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { TechnicalSignal } from "@/lib/signal-utils"

interface TechnicalSignalMeterProps {
  signal: TechnicalSignal
  className?: string
}

export function TechnicalSignalMeter({ signal, className }: TechnicalSignalMeterProps) {
  const { score, bias, strength, signals } = signal

  // Color based on bias
  const biasColor = bias === 'BULLISH' ? 'text-emerald-500' : 
                    bias === 'BEARISH' ? 'text-rose-500' : 'text-slate-400'
  
  const bgColor = bias === 'BULLISH' ? 'bg-emerald-500' : 
                  bias === 'BEARISH' ? 'bg-rose-500' : 'bg-slate-500'

  const borderColor = bias === 'BULLISH' ? 'border-emerald-500/20' : 
                      bias === 'BEARISH' ? 'border-rose-500/20' : 'border-slate-500/20'

  return (
    <Card className={cn("bg-slate-900/50 border-slate-800", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5 text-blue-500" />
              Technical Signal Strength
            </CardTitle>
            <CardDescription>Aggregated from 50+ technical indicators</CardDescription>
          </div>
          <div className="text-right">
            <div className={cn("text-4xl font-black", biasColor)}>
              {score.toFixed(0)}
            </div>
            <div className="text-xs text-slate-500">/ 100</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={cn("h-full transition-all duration-500", bgColor)}
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-sm">
            <Badge variant="outline" className={cn("border-none", 
              bias === 'BULLISH' && "bg-emerald-500/10 text-emerald-400",
              bias === 'BEARISH' && "bg-rose-500/10 text-rose-400",
              bias === 'NEUTRAL' && "bg-slate-500/10 text-slate-400"
            )}>
              {bias}
            </Badge>
            <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-700">
              {strength} STRENGTH
            </Badge>
          </div>
        </div>

        {/* Signal Breakdown */}
        <div className="grid grid-cols-2 gap-4">
          {/* Trend */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-slate-950/50")}>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium text-slate-300">Trend</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold", 
                signals.trend.direction === 'UP' ? "text-emerald-500" :
                signals.trend.direction === 'DOWN' ? "text-rose-500" : "text-slate-400"
              )}>
                {signals.trend.direction}
              </span>
              <span className="text-xs text-slate-500">
                {signals.trend.bullish}/{signals.trend.total}
              </span>
            </div>
          </div>

          {/* Momentum */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-slate-950/50")}>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium text-slate-300">Momentum</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.momentum.state === 'STRONG' || signals.momentum.state === 'OVERSOLD' ? "text-emerald-500" :
                signals.momentum.state === 'WEAK' || signals.momentum.state === 'OVERBOUGHT' ? "text-rose-500" : 
                "text-slate-400"
              )}>
                {signals.momentum.state}
              </span>
              <span className="text-xs text-slate-500">
                {signals.momentum.bullish}/{signals.momentum.total}
              </span>
            </div>
          </div>

          {/* Volume */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-slate-950/50")}>
            <div className="flex items-center gap-2 mb-2">
              <Volume2 className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium text-slate-300">Volume</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.volume.state === 'ACCUMULATION' ? "text-emerald-500" :
                signals.volume.state === 'DISTRIBUTION' ? "text-rose-500" : "text-slate-400"
              )}>
                {signals.volume.state}
              </span>
              <span className="text-xs text-slate-500">
                {signals.volume.bullish}/{signals.volume.total}
              </span>
            </div>
          </div>

          {/* Volatility */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-slate-950/50")}>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-cyan-500" />
              <span className="text-sm font-medium text-slate-300">Volatility</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.volatility.level === 'HIGH' ? "text-rose-500" :
                signals.volatility.level === 'LOW' ? "text-emerald-500" : "text-slate-400"
              )}>
                {signals.volatility.level}
              </span>
            </div>
          </div>
        </div>

        {/* Interpretation */}
        <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
          <p className="text-sm text-blue-300">
            <strong>Interpretation:</strong> {getInterpretation(signal)}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

function getInterpretation(signal: TechnicalSignal): string {
  const { bias, strength, score, signals } = signal

  if (bias === 'BULLISH') {
    if (strength === 'STRONG') {
      return `Strong bullish momentum with ${signals.trend.bullish}/${signals.trend.total} trend indicators confirming upward movement. Consider this a high-conviction buy signal.`
    }
    if (strength === 'MODERATE') {
      return `Moderate bullish bias with positive trend but mixed momentum. Good for accumulation on dips.`
    }
    return `Weak bullish signal with limited conviction. Wait for stronger confirmation before entering.`
  }

  if (bias === 'BEARISH') {
    if (strength === 'STRONG') {
      return `Strong bearish pressure with ${signals.trend.bullish}/${signals.trend.total} trend indicators showing downward movement. Consider reducing exposure or shorting.`
    }
    if (strength === 'MODERATE') {
      return `Moderate bearish bias with negative trend. Avoid new long positions and consider taking profits.`
    }
    return `Weak bearish signal with limited downside conviction. Monitor closely but no immediate action needed.`
  }

  return `Neutral market with no clear directional bias. Indicators are mixed - wait for clearer signals before taking positions.`
}
