"use client";

import React, { lazy, Suspense, useEffect } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { markPerformance, measurePerformance } from '@/lib/performance';

// Lazy load heavy chart components
const ConvictionTimeline = lazy(() => import('@/components/quad/conviction-timeline'));
const PillarDrift = lazy(() => import('@/components/quad/pillar-drift'));
const DecisionHistory = lazy(() => import('@/components/quad/decision-history'));

export default function QuadAnalyticsPage() {
    const [selectedSymbol, setSelectedSymbol] = React.useState('RELIANCE');

    useEffect(() => {
        markPerformance('quad-analytics-loaded');
        measurePerformance('quad-analytics');
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold">QUAD Analytics</h1>
                <div className="flex items-center gap-4">
                    <label className="text-sm text-slate-400">Symbol:</label>
                    <select
                        value={selectedSymbol}
                        onChange={(e) => setSelectedSymbol(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                    >
                        <option value="RELIANCE">RELIANCE</option>
                        <option value="TCS">TCS</option>
                        <option value="INFY">INFY</option>
                        <option value="HDFCBANK">HDFCBANK</option>
                        <option value="ICICIBANK">ICICIBANK</option>
                    </select>
                </div>
            </div>

            {/* Top Row: Timeline and Drift */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Suspense fallback={<ChartSkeleton />}>
                    <ConvictionTimeline symbol={selectedSymbol} days={30} />
                </Suspense>
                <Suspense fallback={<ChartSkeleton />}>
                    <PillarDrift symbol={selectedSymbol} />
                </Suspense>
            </div>

            {/* Bottom Row: Decision History */}
            <Suspense fallback={<TableSkeleton />}>
                <DecisionHistory symbol={selectedSymbol} limit={10} />
            </Suspense>
        </div>
    );
}

function ChartSkeleton() {
    return (
        <div className="border rounded-lg p-6 space-y-4">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-[300px] w-full" />
        </div>
    );
}

function TableSkeleton() {
    return (
        <div className="border rounded-lg p-6 space-y-4">
            <Skeleton className="h-6 w-48" />
            <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                ))}
            </div>
        </div>
    );
}
