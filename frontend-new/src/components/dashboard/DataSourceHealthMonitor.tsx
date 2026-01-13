'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Activity, CheckCircle2, XCircle, AlertCircle, Database, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DataSourceStatus {
    name: string;
    status: 'healthy' | 'degraded' | 'down';
    lastUpdate?: string;
    latency?: number;
    message?: string;
}

interface HealthStatus {
    sources: DataSourceStatus[];
    overall_status: 'healthy' | 'degraded' | 'critical';
    last_check: string;
}

export default function DataSourceHealthMonitor() {
    const [health, setHealth] = useState<HealthStatus | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchHealthStatus();
        // Refresh every 30 seconds
        const interval = setInterval(fetchHealthStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    async function fetchHealthStatus() {
        try {
            const response = await fetch('/api/v1/health/datasources');
            if (response.ok) {
                const data = await response.json();
                setHealth(data);
            } else {
                // Fallback to checking individual sources
                setHealth(await checkDataSources());
            }
        } catch (error) {
            console.error('Failed to fetch data source health:', error);
            setHealth(await checkDataSources());
        } finally {
            setLoading(false);
        }
    }

    async function checkDataSources(): Promise<HealthStatus> {
        const sources: DataSourceStatus[] = [];
        let overall: 'healthy' | 'degraded' | 'critical' = 'healthy';

        // Check OpenAlgo
        try {
            const start = Date.now();
            const res = await fetch('/api/v1/openalgo/health', { method: 'GET' });
            const latency = Date.now() - start;
            sources.push({
                name: 'OpenAlgo (Live Market Data)',
                status: res.ok ? 'healthy' : 'down',
                latency,
                lastUpdate: new Date().toISOString(),
                message: res.ok ? 'Real-time feed active' : 'Connection failed'
            });
            if (!res.ok) overall = 'critical';
        } catch {
            sources.push({
                name: 'OpenAlgo (Live Market Data)',
                status: 'down',
                message: 'Service unreachable'
            });
            overall = 'critical';
        }

        // Check NSE Historical
        try {
            const start = Date.now();
            const res = await fetch('/api/v1/health/nse', { method: 'GET' });
            const latency = Date.now() - start;
            sources.push({
                name: 'NSE Historical Data',
                status: res.ok ? 'healthy' : 'degraded',
                latency,
                lastUpdate: new Date().toISOString(),
                message: res.ok ? 'Historical data available' : 'Limited availability'
            });
            if (!res.ok && overall === 'healthy') overall = 'degraded';
        } catch {
            sources.push({
                name: 'NSE Historical Data',
                status: 'degraded',
                message: 'API timeout'
            });
            if (overall === 'healthy') overall = 'degraded';
        }

        // Check PostgreSQL
        try {
            const start = Date.now();
            const res = await fetch('/api/v1/health', { method: 'GET' });
            const latency = Date.now() - start;
            sources.push({
                name: 'PostgreSQL Database',
                status: res.ok ? 'healthy' : 'down',
                latency,
                lastUpdate: new Date().toISOString(),
                message: res.ok ? 'Database operational' : 'Connection failed'
            });
            if (!res.ok) overall = 'critical';
        } catch {
            sources.push({
                name: 'PostgreSQL Database',
                status: 'down',
                message: 'Database unreachable'
            });
            overall = 'critical';
        }

        // Check Redis
        try {
            const res = await fetch('/api/v1/health/redis', { method: 'GET' });
            sources.push({
                name: 'Redis Cache',
                status: res.ok ? 'healthy' : 'degraded',
                lastUpdate: new Date().toISOString(),
                message: res.ok ? 'Cache active' : 'Cache unavailable'
            });
            if (!res.ok && overall === 'healthy') overall = 'degraded';
        } catch {
            sources.push({
                name: 'Redis Cache',
                status: 'degraded',
                message: 'Cache offline'
            });
            if (overall === 'healthy') overall = 'degraded';
        }

        return {
            sources,
            overall_status: overall,
            last_check: new Date().toISOString()
        };
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'healthy':
                return <CheckCircle2 className="w-4 h-4 text-success" />;
            case 'degraded':
                return <AlertCircle className="w-4 h-4 text-warning" />;
            case 'down':
                return <XCircle className="w-4 h-4 text-destructive" />;
            default:
                return <Activity className="w-4 h-4 text-muted-foreground" />;
        }
    };

    const getStatusBadgeClass = (status: string) => {
        switch (status) {
            case 'healthy':
                return 'bg-success/10 text-success border-success/20';
            case 'degraded':
                return 'bg-warning/10 text-warning border-warning/20';
            case 'down':
                return 'bg-destructive/10 text-destructive border-destructive/20';
            default:
                return 'bg-muted text-muted-foreground border-border';
        }
    };

    if (loading || !health) {
        return (
            <Card className="bg-card border-border">
                <CardHeader className="py-3 border-b border-border">
                    <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground font-black flex items-center gap-2">
                        <Database className="w-4 h-4 text-primary" />
                        Data Sources
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 flex items-center justify-center h-32">
                    <Activity className="w-6 h-6 text-primary animate-pulse" />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="bg-card border-border">
            <CardHeader className="py-3 border-b border-border">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-xs uppercase tracking-widest text-muted-foreground font-black flex items-center gap-2">
                        <Database className="w-4 h-4 text-primary" />
                        Data Sources
                    </CardTitle>
                    <div className={cn(
                        "text-[8px] font-bold px-2 py-1 rounded border uppercase tracking-tight",
                        getStatusBadgeClass(health.overall_status)
                    )}>
                        {health.overall_status}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <div className="divide-y divide-border">
                    {health.sources.map((source, index) => (
                        <div key={index} className="p-3 hover:bg-muted/5 transition-colors">
                            <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(source.status)}
                                    <span className="text-xs font-semibold text-foreground">{source.name}</span>
                                </div>
                                {source.latency && (
                                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                                        <Clock className="w-3 h-3" />
                                        {source.latency}ms
                                    </div>
                                )}
                            </div>
                            <div className="text-[10px] text-muted-foreground ml-6">
                                {source.message || 'No status message'}
                            </div>
                            {source.lastUpdate && (
                                <div className="text-[9px] text-muted-foreground/60 ml-6 mt-0.5">
                                    Updated: {new Date(source.lastUpdate).toLocaleTimeString()}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
                <div className="p-2 bg-muted/20 border-t border-border">
                    <div className="text-[8px] text-muted-foreground text-center uppercase tracking-widest">
                        Last Check: {new Date(health.last_check).toLocaleTimeString()}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
