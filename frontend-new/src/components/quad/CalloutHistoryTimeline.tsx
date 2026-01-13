
import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api/client';

import { Activity, ArrowUpRight, ArrowDownRight, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface Alert {
    alert_type: string;
    level: string;
    symbol: string;
    message: string;
    metadata: string | object; // It comes as stringified JSON from DB sometimes
    created_at: string;
}

interface TimelineProps {
    symbol?: string;
    days?: number;
}

const CalloutHistoryTimeline: React.FC<TimelineProps> = ({ symbol, days }) => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchAlerts = async () => {
        try {
            const response = await api.get('/alerts/recent?limit=50');
            const data: Alert[] = response.data;

            // Filter for Callouts AND Symbol if provided
            const callouts = data.filter(a => {
                const isCallout = a.alert_type && (a.alert_type.includes('CALLOUT') || a.alert_type.includes('ACCELERATION') || a.alert_type.includes('DETERIORATION'));
                const matchesSymbol = symbol ? a.symbol === symbol : true;
                return isCallout && matchesSymbol;
            });

            setAlerts(callouts);
            setLoading(false);
        } catch (error) {
            console.error("Failed to fetch alerts:", error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const getMetadata = (alert: Alert) => {
        if (typeof alert.metadata === 'string') {
            try {
                return JSON.parse(alert.metadata);
            } catch {
                return {};
            }
        }
        return alert.metadata || {};
    };

    return (
        <Card className="h-[400px] flex flex-col">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                    <span className="flex items-center gap-2">
                        <Activity className="h-5 w-5 text-indigo-500" />
                        Conviction Timeline
                    </span>
                    <Badge variant="outline" className="text-xs">
                        Live
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                        Loading timeline...
                    </div>
                ) : alerts.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                        No recent conviction events
                    </div>
                ) : (
                    <ScrollArea className="h-full px-4">
                        <div className="space-y-4 py-4">
                            {alerts.map((alert, idx) => {
                                const meta = getMetadata(alert);
                                const isPositive = alert.alert_type.includes('ACCELERATION') || (meta.delta && meta.delta > 0);
                                const isNegative = alert.alert_type.includes('DETERIORATION') || (meta.delta && meta.delta < 0);

                                return (
                                    <div key={idx} className="relative flex gap-4 text-sm group">
                                        {/* Timeline Line */}
                                        <div className="absolute left-[11px] top-8 bottom-[-16px] w-[2px] bg-muted group-last:hidden" />

                                        {/* Icon Bubble */}
                                        <div
                                            className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border 
                        ${isPositive ? 'bg-green-100 border-green-200 text-green-600' :
                                                    isNegative ? 'bg-red-100 border-red-200 text-red-600' : 'bg-gray-100 border-gray-200'}
                      `}
                                        >
                                            {isPositive ? <ArrowUpRight className="h-3 w-3" /> :
                                                isNegative ? <ArrowDownRight className="h-3 w-3" /> : <Activity className="h-3 w-3" />}
                                        </div>

                                        {/* Content */}
                                        <div className="flex flex-col gap-1 pb-2 w-full">
                                            <div className="flex items-center justify-between">
                                                <span className="font-semibold font-mono text-primary">{alert.symbol || "UNK"}</span>
                                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    {format(new Date(alert.created_at || new Date()), 'hh:mm:ss a')}
                                                </span>
                                            </div>

                                            <p className="text-xs text-muted-foreground leading-tight">
                                                {alert.message.replace(alert.symbol || '', '').replace('🚀', '').replace('⚠️', '').trim()}
                                            </p>

                                            {meta.delta && (
                                                <div className="flex gap-2 mt-1">
                                                    <Badge variant="secondary" className="text-[10px] h-4 px-1">
                                                        Δ {meta.delta > 0 ? '+' : ''}{meta.delta.toFixed(1)}
                                                    </Badge>
                                                    <Badge variant="secondary" className="text-[10px] h-4 px-1 bg-muted/50">
                                                        Score: {meta.current_score?.toFixed(1) || '?'}
                                                    </Badge>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </ScrollArea>
                )}
            </CardContent>
        </Card>
    );
};

export default CalloutHistoryTimeline;
