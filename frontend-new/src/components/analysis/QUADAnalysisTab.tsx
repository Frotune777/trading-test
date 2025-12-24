/**
 * QUAD Analysis Tab Component
 * 
 * Displays AI-powered QUAD reasoning with pillar scores and conviction
 */

'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, TrendingUp, DollarSign, Zap, AlertTriangle, CheckCircle2, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

interface QUADPillar {
  score: number
  bias: string
  is_placeholder: boolean
  weight: number
  metrics: Record<string, any>
}

interface QUADReasoning {
  symbol: string
  conviction_score: number
  directional_bias: string
  pillar_scores: {
    trend?: QUADPillar
    momentum?: QUADPillar
    volatility?: QUADPillar
    liquidity?: QUADPillar
    sentiment?: QUADPillar
    regime?: QUADPillar
  }
  warnings: string[]
  is_execution_ready: boolean
  error?: string
}

interface QUADAnalysisTabProps {
  data: QUADReasoning
  isLoading?: boolean
}

export function QUADAnalysisTab({ data, isLoading }: QUADAnalysisTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
        <span className="ml-3 text-slate-600 dark:text-slate-400">Loading QUAD analysis...</span>
      </div>
    )
  }

  if (data?.error) {
    return (
      <Card className="bg-rose-50 dark:bg-rose-500/5 border-rose-200 dark:border-rose-500/20">
        <CardContent className="py-12 flex flex-col items-center justify-center text-center">
          <AlertTriangle className="h-10 w-10 text-rose-500 mb-4" />
          <h3 className="text-rose-700 dark:text-rose-400 font-bold mb-2">Analysis Failed</h3>
          <p className="text-rose-600 dark:text-rose-300/70 text-sm max-w-md" data-testid="analysis-error-message">
            {data.error}
          </p>
        </CardContent>
      </Card>
    )
  }

  if (!data || !data.pillar_scores) {
    return (
      <div className="text-center py-12 text-slate-600 dark:text-slate-500" data-testid="no-analysis-message">
        No QUAD analysis available for this symbol
      </div>
    )
  }

  const { conviction_score: conviction, directional_bias: bias, pillar_scores: pillars, warnings, is_execution_ready } = data

  const biasColor = bias === 'BULLISH' ? 'text-emerald-500' :
    bias === 'BEARISH' ? 'text-rose-500' : 'text-slate-400'

  return (
    <div className="space-y-6">
      {/* Conviction Meter */}
      <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-slate-900 dark:text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-500" />
                QUAD Conviction Score
              </CardTitle>
              <CardDescription>AI-powered multi-factor analysis</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-5xl font-black text-blue-400" data-testid="conviction-score">
                {conviction?.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-500">/ 100</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{ width: `${conviction}%` }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className={cn("border-none text-lg px-4 py-1",
                bias === 'BULLISH' && "bg-emerald-500/10 text-emerald-400",
                bias === 'BEARISH' && "bg-rose-500/10 text-rose-400",
                bias === 'NEUTRAL' && "bg-slate-500/10 text-slate-400"
              )} data-testid="directional-bias">
                {bias}
              </Badge>
              <div className="flex flex-col items-end">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {conviction > 70 ? 'High Conviction' : conviction > 40 ? 'Moderate Conviction' : 'Low Conviction'}
                </span>
                <span className={cn("text-[10px] font-bold uppercase", is_execution_ready ? "text-emerald-500" : "text-amber-500")}>
                  {is_execution_ready ? "Execution Ready" : "Manual Review Needed"}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Four Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Trend Pillar */}
        {pillars?.trend && (
          <PillarCard
            title="Trend"
            icon={<TrendingUp className="h-5 w-5 text-blue-500" />}
            score={pillars.trend.score}
            bias={pillars.trend.bias}
            is_placeholder={pillars.trend.is_placeholder}
            color="blue"
          />
        )}

        {/* Momentum Pillar */}
        {pillars?.momentum && (
          <PillarCard
            title="Momentum"
            icon={<Zap className="h-5 w-5 text-purple-500" />}
            score={pillars.momentum.score}
            bias={pillars.momentum.bias}
            is_placeholder={pillars.momentum.is_placeholder}
            color="purple"
          />
        )}

        {/* Volatility Pillar */}
        {pillars?.volatility && (
          <PillarCard
            title="Volatility"
            icon={<Activity className="h-5 w-5 text-cyan-500" />}
            score={pillars.volatility.score}
            bias={pillars.volatility.bias}
            is_placeholder={pillars.volatility.is_placeholder}
            color="emerald"
          />
        )}

        {/* Regime Pillar */}
        {pillars?.regime && (
          <PillarCard
            title="Regime"
            icon={<Shield className="h-5 w-5 text-orange-500" />}
            score={pillars.regime.score}
            bias={pillars.regime.bias}
            is_placeholder={pillars.regime.is_placeholder}
            color="orange"
          />
        )}
      </div>

      {/* Warnings */}
      {warnings && warnings.length > 0 && warnings[0] !== 'None' && (
        <Card className="bg-rose-50 dark:bg-rose-500/5 border-rose-200 dark:border-rose-500/20">
          <CardHeader>
            <CardTitle className="text-rose-700 dark:text-rose-400 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Warnings & Risk Factors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {warnings.map((warning, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-rose-700 dark:text-rose-300">
                  <span className="text-rose-500 mt-0.5">•</span>
                  <span>{warning}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

interface PillarCardProps {
  title: string
  icon: React.ReactNode
  score: number
  bias: string
  is_placeholder: boolean
  color: 'emerald' | 'blue' | 'purple' | 'orange'
}

function PillarCard({ title, icon, score, bias, is_placeholder, color }: PillarCardProps) {
  const colorClasses = {
    emerald: {
      bg: 'bg-emerald-500',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400'
    },
    blue: {
      bg: 'bg-blue-500',
      border: 'border-blue-500/20',
      text: 'text-blue-400'
    },
    purple: {
      bg: 'bg-purple-500',
      border: 'border-purple-500/20',
      text: 'text-purple-400'
    },
    orange: {
      bg: 'bg-orange-500',
      border: 'border-orange-500/20',
      text: 'text-orange-400'
    }
  }

  const classes = colorClasses[color]

  return (
    <Card className={cn("bg-white dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-colors", classes.border)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-slate-900 dark:text-white text-lg">{title}</CardTitle>
          </div>
          <div className={cn("text-3xl font-bold", classes.text)}>
            {score}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className={cn("h-full transition-all duration-500", classes.bg)}
              style={{ width: `${score}%` }}
            />
          </div>
          <div className="flex items-center justify-between">
            <Badge variant="outline" className={cn("border-none",
              bias === 'BULLISH' && "bg-emerald-500/10 text-emerald-400",
              bias === 'BEARISH' && "bg-rose-500/10 text-rose-400",
              bias === 'NEUTRAL' && "bg-slate-500/10 text-slate-400"
            )}>
              {bias}
            </Badge>
            {is_placeholder && (
              <Badge variant="secondary" className="bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-500 text-[10px]">
                PLACEHOLDER
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
