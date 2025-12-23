/**
 * QUAD Analysis Tab Component
 * 
 * Displays AI-powered QUAD reasoning with pillar scores and conviction
 */

'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, TrendingUp, DollarSign, Zap, AlertTriangle, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface QUADPillar {
  score: number
  reasoning: string
}

interface QUADReasoning {
  symbol: string
  conviction: number
  bias: string
  pillars: {
    quality: QUADPillar
    undervaluation: QUADPillar
    acceleration: QUADPillar
    directional: QUADPillar
  }
  warnings: string[]
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
        <span className="ml-3 text-slate-400">Loading QUAD analysis...</span>
      </div>
    )
  }

  if (!data || !data.pillars) {
    return (
      <div className="text-center py-12 text-slate-500">
        No QUAD analysis available for this symbol
      </div>
    )
  }

  const { conviction, bias, pillars, warnings } = data

  const biasColor = bias === 'BUY' ? 'text-emerald-500' : 
                    bias === 'SELL' ? 'text-rose-500' : 'text-slate-400'

  return (
    <div className="space-y-6">
      {/* Conviction Meter */}
      <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-500/20">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-500" />
                QUAD Conviction Score
              </CardTitle>
              <CardDescription>AI-powered multi-factor analysis</CardDescription>
            </div>
            <div className="text-right">
              <div className="text-5xl font-black text-blue-400">
                {conviction}
              </div>
              <div className="text-xs text-slate-500">/ 100</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{ width: `${conviction}%` }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className={cn("border-none text-lg px-4 py-1",
                bias === 'BUY' && "bg-emerald-500/10 text-emerald-400",
                bias === 'SELL' && "bg-rose-500/10 text-rose-400",
                bias === 'HOLD' && "bg-slate-500/10 text-slate-400"
              )}>
                {bias}
              </Badge>
              <span className="text-sm text-slate-400">
                {conviction > 70 ? 'High Conviction' : conviction > 40 ? 'Moderate Conviction' : 'Low Conviction'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Four Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Quality Pillar */}
        {pillars?.quality && (
          <PillarCard
            title="Quality"
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-500" />}
            score={pillars.quality.score}
            reasoning={pillars.quality.reasoning}
            color="emerald"
          />
        )}

        {/* Undervaluation Pillar */}
        {pillars?.undervaluation && (
          <PillarCard
            title="Undervaluation"
            icon={<DollarSign className="h-5 w-5 text-blue-500" />}
            score={pillars.undervaluation.score}
            reasoning={pillars.undervaluation.reasoning}
            color="blue"
          />
        )}

        {/* Acceleration Pillar */}
        {pillars?.acceleration && (
          <PillarCard
            title="Acceleration"
            icon={<Zap className="h-5 w-5 text-purple-500" />}
            score={pillars.acceleration.score}
            reasoning={pillars.acceleration.reasoning}
            color="purple"
          />
        )}

        {/* Directional Pillar */}
        {pillars?.directional && (
          <PillarCard
            title="Directional"
            icon={<TrendingUp className="h-5 w-5 text-orange-500" />}
            score={pillars.directional.score}
            reasoning={pillars.directional.reasoning}
            color="orange"
          />
        )}
      </div>

      {/* Warnings */}
      {warnings && warnings.length > 0 && warnings[0] !== 'None' && (
        <Card className="bg-rose-500/5 border-rose-500/20">
          <CardHeader>
            <CardTitle className="text-rose-400 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Warnings & Risk Factors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {warnings.map((warning, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-rose-300">
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
  reasoning: string
  color: 'emerald' | 'blue' | 'purple' | 'orange'
}

function PillarCard({ title, icon, score, reasoning, color }: PillarCardProps) {
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
    <Card className={cn("bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors", classes.border)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-white text-lg">{title}</CardTitle>
          </div>
          <div className={cn("text-3xl font-bold", classes.text)}>
            {score}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={cn("h-full transition-all duration-500", classes.bg)}
              style={{ width: `${score}%` }}
            />
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {reasoning}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
