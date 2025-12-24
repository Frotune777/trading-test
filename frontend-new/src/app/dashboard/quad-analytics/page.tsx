"use client";

import React from 'react';
import ConvictionTimeline from '@/components/quad/conviction-timeline';
import PillarDrift from '@/components/quad/pillar-drift';
import DecisionHistory from '@/components/quad/decision-history';

export default function QuadAnalyticsPage() {
    const [selectedSymbol, setSelectedSymbol] = React.useState('RELIANCE');

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
                <ConvictionTimeline symbol={selectedSymbol} days={30} />
                <PillarDrift symbol={selectedSymbol} />
            </div>

            {/* Bottom Row: Decision History */}
            <DecisionHistory symbol={selectedSymbol} limit={10} />
        </div>
    );
}
