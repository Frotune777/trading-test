"use client";

import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

interface Props {
    symbol: string;
    timeframe?: string;
}

const CandlestickChart: React.FC<Props> = ({ symbol, timeframe: initialTimeframe = '1D' }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState(initialTimeframe);

    const timeframes = ['1D', '1W', '1M', '3M', '6M', '1Y'];

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#0f172a' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 450,
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });

        // Mock Data (varies by timeframe)
        const mockData = selectedTimeframe === '1D' ? [
            { time: '2024-01-01', open: 2100, high: 2150, low: 2090, close: 2140 },
            { time: '2024-01-02', open: 2140, high: 2160, low: 2130, close: 2155 },
            { time: '2024-01-03', open: 2155, high: 2170, low: 2145, close: 2150 },
            { time: '2024-01-04', open: 2150, high: 2180, low: 2140, close: 2175 },
        ] : [
            { time: '2023-01-01', open: 1800, high: 2000, low: 1750, close: 1950 },
            { time: '2023-06-01', open: 1950, high: 2100, low: 1900, close: 2050 },
            { time: '2024-01-01', open: 2050, high: 2200, low: 2000, close: 2175 },
        ];

        candlestickSeries.setData(mockData);
        chart.timeScale().fitContent();

        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current?.clientWidth });
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [symbol, selectedTimeframe]);

    return (
        <div className="w-full h-full flex flex-col gap-3">
            {/* Timeframe Selector */}
            <div className="flex gap-2 justify-end px-4">
                {timeframes.map((tf) => (
                    <button
                        key={tf}
                        onClick={() => setSelectedTimeframe(tf)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${selectedTimeframe === tf
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                            }`}
                    >
                        {tf}
                    </button>
                ))}
            </div>

            <div ref={chartContainerRef} className="w-full h-full" />
        </div>
    );
};

export default CandlestickChart;
