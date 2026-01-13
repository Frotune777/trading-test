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
import { cn } from '@/lib/utils';

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

interface EndpointStat {
  endpoint: string;
  method: string;
  count: number;
  avg_response_time_ms: number;
  errors: number;
  error_rate: number;
}

export function MonitoringDashboard() {
  const [stats, setStats] = useState<MonitoringStats>({
    latency: { avg: 0, p50: 0, p95: 0, p99: 0 },
    traffic: { total_requests: 0, error_rate: 0, avg_response_time_ms: 0 },
    pnl: { total_pnl: 0, day_pnl: 0, realized_pnl: 0, unrealized_pnl: 0 }
  });
  const [endpointStats, setEndpointStats] = useState<EndpointStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const [latencyRes, trafficRes, pnlRes, endpointsRes] = await Promise.all([
        fetch('/api/v1/monitoring/latency/stats'),
        fetch('/api/v1/monitoring/traffic'),
        fetch('/api/v1/monitoring/pnl/1'), // TODO: Get user ID from auth
        fetch('/api/v1/monitoring/traffic/endpoints'),
      ]);

      const newStats = { ...stats };

      if (latencyRes.ok) {
        newStats.latency = await latencyRes.json();
      }
      if (trafficRes.ok) {
        newStats.traffic = await trafficRes.json();
      }

      if (pnlRes.ok) {
        const pnl = await pnlRes.json();
        newStats.pnl = pnl;
      }

      if (endpointsRes.ok) {
        const endpointsData = await endpointsRes.json();
        setEndpointStats(endpointsData.endpoints || []);
      }

      setStats(prev => ({ ...prev, ...newStats }));
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch monitoring stats:', error);
      // Keep existing stats or safe defaults on error
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
              className={`text-2xl font-bold ${(stats?.pnl.total_pnl || 0) >= 0
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
              className={`text-2xl font-bold ${(stats?.pnl.unrealized_pnl || 0) >= 0
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

      {/* Endpoint Health Table */}
      <Card>
        <CardHeader>
          <CardTitle>Endpoint Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50">
                <tr>
                  <th className="px-4 py-2">Endpoint</th>
                  <th className="px-4 py-2">Method</th>
                  <th className="px-4 py-2">Requests</th>
                  <th className="px-4 py-2">Errors</th>
                  <th className="px-4 py-2">Rate</th>
                  <th className="px-4 py-2">Latency</th>
                </tr>
              </thead>
              <tbody>
                {endpointStats.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-2 text-center text-muted-foreground">No traffic data available</td>
                  </tr>
                ) : (
                  endpointStats.map((stat, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-muted/50">
                      <td className="px-4 py-2 font-mono text-xs">{stat.endpoint}</td>
                      <td className="px-4 py-2 text-xs">{stat.method}</td>
                      <td className="px-4 py-2">{stat.count}</td>
                      <td className={cn("px-4 py-2", stat.errors > 0 ? "text-destructive font-bold" : "")}>{stat.errors}</td>
                      <td className={cn("px-4 py-2", stat.error_rate > 5 ? "text-destructive font-bold" : "")}>{stat.error_rate}%</td>
                      <td className="px-4 py-2">{stat.avg_response_time_ms}ms</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

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
