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
  const biasColor = bias === 'BULLISH' ? 'text-success' : 
                    bias === 'BEARISH' ? 'text-destructive' : 'text-muted-foreground'
  
  const bgColor = bias === 'BULLISH' ? 'bg-success' : 
                  bias === 'BEARISH' ? 'bg-destructive' : 'bg-muted'

  const borderColor = bias === 'BULLISH' ? 'border-success/20' : 
                      bias === 'BEARISH' ? 'border-destructive/20' : 'border-border'

  return (
    <Card className={cn("bg-card border-border", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-foreground flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Technical Signal Strength
            </CardTitle>
            <CardDescription>Aggregated from 50+ technical indicators</CardDescription>
          </div>
          <div className="text-right">
            <div className={cn("text-4xl font-black", biasColor)}>
              {score.toFixed(0)}
            </div>
            <div className="text-xs text-muted-foreground">/ 100</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="h-4 bg-secondary rounded-full overflow-hidden">
            <div 
              className={cn("h-full transition-all duration-500", bgColor)}
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-sm">
            <Badge variant="outline" className={cn("border-none", 
              bias === 'BULLISH' && "bg-success/10 text-success",
              bias === 'BEARISH' && "bg-destructive/10 text-destructive",
              bias === 'NEUTRAL' && "bg-muted/10 text-muted-foreground"
            )}>
              {bias}
            </Badge>
            <Badge variant="outline" className="bg-secondary text-muted-foreground border-border">
              {strength} STRENGTH
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Trend */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-muted/50")}>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">Trend</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold", 
                signals.trend.direction === 'UP' ? "text-success" :
                signals.trend.direction === 'DOWN' ? "text-destructive" : "text-muted-foreground"
              )}>
                {signals.trend.direction}
              </span>
              <span className="text-xs text-muted-foreground">
                {signals.trend.bullish}/{signals.trend.total}
              </span>
            </div>
          </div>

          {/* Momentum */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-muted/50")}>
            <div className="flex items-center gap-2 mb-2">
              <Activity className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">Momentum</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.momentum.state === 'STRONG' || signals.momentum.state === 'OVERSOLD' ? "text-success" :
                signals.momentum.state === 'WEAK' || signals.momentum.state === 'OVERBOUGHT' ? "text-destructive" : 
                "text-muted-foreground"
              )}>
                {signals.momentum.state}
              </span>
              <span className="text-xs text-muted-foreground">
                {signals.momentum.bullish}/{signals.momentum.total}
              </span>
            </div>
          </div>

          {/* Volume */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-muted/50")}>
            <div className="flex items-center gap-2 mb-2">
              <Volume2 className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">Volume</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.volume.state === 'ACCUMULATION' ? "text-success" :
                signals.volume.state === 'DISTRIBUTION' ? "text-destructive" : "text-muted-foreground"
              )}>
                {signals.volume.state}
              </span>
              <span className="text-xs text-muted-foreground">
                {signals.volume.bullish}/{signals.volume.total}
              </span>
            </div>
          </div>

          {/* Volatility */}
          <div className={cn("p-4 rounded-lg border", borderColor, "bg-muted/50")}>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">Volatility</span>
            </div>
            <div className="flex items-center justify-between">
              <span className={cn("text-lg font-bold",
                signals.volatility.level === 'HIGH' ? "text-destructive" :
                signals.volatility.level === 'LOW' ? "text-success" : "text-muted-foreground"
              )}>
                {signals.volatility.level}
              </span>
            </div>
          </div>
        </div>

        {/* Interpretation */}
        <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
          <p className="text-sm text-primary">
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
