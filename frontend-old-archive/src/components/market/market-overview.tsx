"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';

interface MarketIndex {
    name: string;
    value: string;
    change: string;
    up: boolean;
}

export default function MarketOverview() {
    const [indexes, setIndexes] = useState<MarketIndex[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Assuming backend is on port 8000. In prod, use env var.
                const response = await fetch('http://localhost:8000/api/v1/data/indices');
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                setIndexes(data);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch market indices:", err);
                setError(true);
                setLoading(false);
            }
        };

        fetchData();
        // Refresh every minute
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i} className="bg-slate-900 border-slate-800 animate-pulse">
                        <CardHeader className="pb-2"><div className="h-4 w-20 bg-slate-700 rounded"></div></CardHeader>
                        <CardContent><div className="h-8 w-32 bg-slate-700 rounded"></div></CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (error) {
        // Fallback to static if API fails (graceful degradation)
        const fallbackIndexes = [
            { name: 'NIFTY 50', value: 'N/A', change: '0.0%', up: true },
            { name: 'SENSEX', value: 'N/A', change: '0.0%', up: true },
        ];
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                {fallbackIndexes.map((idx) => (
                    <Card key={idx.name} className="bg-slate-900 border-slate-800 opacity-70">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-slate-400">{idx.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{idx.value}</div>
                            <p className="text-xs text-slate-500 mt-1">Status: Offline</p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            {indexes.map((idx) => (
                <Card key={idx.name} className="bg-slate-900 border-slate-800">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">{idx.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{idx.value}</div>
                        <p className={`text-xs ${idx.up ? 'text-green-400' : 'text-red-400'} mt-1`}>
                            {idx.change}
                        </p>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
