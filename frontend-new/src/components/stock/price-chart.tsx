"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface PriceData {
    date: string
    close: number
    open: number
    high: number
    low: number
    volume: number
}

interface PriceChartProps {
    data: PriceData[]
    symbol: string
}

export function PriceChart({ data, symbol }: PriceChartProps) {
    if (!data || data.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Price Chart (1Y)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[400px] flex items-center justify-center border border-dashed border-slate-700 rounded-lg text-slate-500">
                        No price data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Format data for chart
    const chartData = data.map(item => ({
        date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        price: item.close,
        volume: item.volume
    }))

    // Calculate price change for color
    const firstPrice = data[0]?.close || 0
    const lastPrice = data[data.length - 1]?.close || 0
    const isPositive = lastPrice >= firstPrice

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <CardTitle className="text-white">Price Chart (1Y)</CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                <stop
                                    offset="5%"
                                    stopColor={isPositive ? "#10b981" : "#ef4444"}
                                    stopOpacity={0.3}
                                />
                                <stop
                                    offset="95%"
                                    stopColor={isPositive ? "#10b981" : "#ef4444"}
                                    stopOpacity={0}
                                />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                            dataKey="date"
                            stroke="#94a3b8"
                            tick={{ fill: '#94a3b8' }}
                        />
                        <YAxis
                            stroke="#94a3b8"
                            tick={{ fill: '#94a3b8' }}
                            domain={['auto', 'auto']}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '8px'
                            }}
                            labelStyle={{ color: '#e2e8f0' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="price"
                            stroke={isPositive ? "#10b981" : "#ef4444"}
                            strokeWidth={2}
                            fill="url(#colorPrice)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
