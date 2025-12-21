"use client"

import { useState } from "react"
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface IntradayData {
    Date: string
    Open: number
    High: number
    Low: number
    Close: number
    Volume: number
}

interface IntradayChartProps {
    data: IntradayData[]
    symbol: string
    onIntervalChange?: (interval: string) => void
}

export function IntradayChart({ data, symbol, onIntervalChange }: IntradayChartProps) {
    const [selectedInterval, setSelectedInterval] = useState('5m')

    const intervals = [
        { value: '1m', label: '1m' },
        { value: '5m', label: '5m' },
        { value: '15m', label: '15m' },
        { value: '30m', label: '30m' },
        { value: '1h', label: '1h' },
    ]

    const handleIntervalChange = (interval: string) => {
        setSelectedInterval(interval)
        onIntervalChange?.(interval)
    }

    if (!data || data.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-white">Intraday Chart</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[400px] flex items-center justify-center border border-dashed border-slate-700 rounded-lg text-slate-500">
                        No intraday data available
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Format data for chart
    const chartData = data.map(item => ({
        time: new Date(item.Date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        price: item.Close,
        volume: item.Volume / 1000, // Convert to thousands
        high: item.High,
        low: item.Low,
        open: item.Open,
        close: item.Close,
    }))

    // Custom candlestick-like rendering using bars
    const CustomCandlestick = (props: any) => {
        const { x, y, width, height, payload } = props
        const isGreen = payload.close >= payload.open
        const color = isGreen ? '#10b981' : '#ef4444'

        return (
            <g>
                <rect
                    x={x}
                    y={y}
                    width={width}
                    height={height}
                    fill={color}
                    opacity={0.8}
                />
            </g>
        )
    }

    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-white">Intraday Chart</CardTitle>
                    <div className="flex gap-2">
                        {intervals.map(interval => (
                            <Button
                                key={interval.value}
                                variant={selectedInterval === interval.value ? "default" : "outline"}
                                size="sm"
                                onClick={() => handleIntervalChange(interval.value)}
                                className={selectedInterval === interval.value
                                    ? "bg-emerald-600 hover:bg-emerald-700"
                                    : "bg-slate-800 hover:bg-slate-700 border-slate-700"}
                            >
                                {interval.label}
                            </Button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                    <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                            dataKey="time"
                            stroke="#94a3b8"
                            tick={{ fill: '#94a3b8', fontSize: 12 }}
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            yAxisId="price"
                            stroke="#94a3b8"
                            tick={{ fill: '#94a3b8' }}
                            domain={['auto', 'auto']}
                        />
                        <YAxis
                            yAxisId="volume"
                            orientation="right"
                            stroke="#94a3b8"
                            tick={{ fill: '#94a3b8' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1e293b',
                                border: '1px solid #334155',
                                borderRadius: '8px'
                            }}
                            labelStyle={{ color: '#e2e8f0' }}
                        />
                        <Legend />
                        <Bar
                            yAxisId="volume"
                            dataKey="volume"
                            fill="#64748b"
                            opacity={0.3}
                            name="Volume (K)"
                        />
                        <Line
                            yAxisId="price"
                            type="monotone"
                            dataKey="price"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={false}
                            name="Price"
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}
