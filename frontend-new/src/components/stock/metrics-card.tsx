"use client"

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface MetricItem {
    label: string
    value: string | number
    suffix?: string
}

interface MetricsCardProps {
    title: string
    metrics: MetricItem[]
}

export function MetricsCard({ title, metrics }: MetricsCardProps) {
    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {metrics.map((metric, index) => (
                        <div key={index} className="flex justify-between items-center">
                            <span className="text-slate-400 text-sm">{metric.label}</span>
                            <span className="text-white font-medium">
                                {metric.value !== null && metric.value !== undefined
                                    ? `${metric.value}${metric.suffix || ''}`
                                    : '--'}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
