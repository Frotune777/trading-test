/**
 * Monitoring Dashboard Component
 * Displays latency, traffic, and P&L metrics
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LatencyChart } from './LatencyChart';
import { TrafficChart } from './TrafficChart';
import { PnLChart } from './PnLChart';

interface MonitoringStats {
  latency: {
    avg: number;
    p50: number;
    p95: number;
    p99: number;
  };
  traffic: {
    total_requests: number;
    error_rate: number;
    avg_response_time_ms: number;
  };
  pnl: {
    total_pnl: number;
    day_pnl: number;
    realized_pnl: number;
    unrealized_pnl: number;
  };
}

export function MonitoringDashboard() {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [latencyRes, trafficRes, pnlRes] = await Promise.all([
        fetch('/api/v1/monitoring/latency/stats'),
        fetch('/api/v1/monitoring/traffic'),
        fetch('/api/v1/monitoring/pnl/1'), // TODO: Get user ID from auth
      ]);

      const latency = await latencyRes.json();
      const traffic = await trafficRes.json();
      const pnl = await pnlRes.json();

      setStats({ latency, traffic, pnl });
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch monitoring stats:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading monitoring data...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">System Monitoring</h1>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-muted-foreground">Live</span>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.latency.avg.toFixed(2)}ms
            </div>
            <p className="text-xs text-muted-foreground">
              p95: {stats?.latency.p95.toFixed(2)}ms
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.traffic.total_requests.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Error rate: {stats?.traffic.error_rate.toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                (stats?.pnl.total_pnl || 0) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}
            >
              ₹{stats?.pnl.total_pnl.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Day: ₹{stats?.pnl.day_pnl.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Unrealized P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                (stats?.pnl.unrealized_pnl || 0) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}
            >
              ₹{stats?.pnl.unrealized_pnl.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Realized: ₹{stats?.pnl.realized_pnl.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="latency" className="space-y-4">
        <TabsList>
          <TabsTrigger value="latency">Latency</TabsTrigger>
          <TabsTrigger value="traffic">Traffic</TabsTrigger>
          <TabsTrigger value="pnl">P&L</TabsTrigger>
        </TabsList>

        <TabsContent value="latency" className="space-y-4">
          <LatencyChart />
        </TabsContent>

        <TabsContent value="traffic" className="space-y-4">
          <TrafficChart />
        </TabsContent>

        <TabsContent value="pnl" className="space-y-4">
          <PnLChart />
        </TabsContent>
      </Tabs>
    </div>
  );
}
