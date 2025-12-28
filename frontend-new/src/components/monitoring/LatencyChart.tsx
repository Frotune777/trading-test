/**
 * Latency Chart Component
 * Displays API latency metrics over time
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LatencyData {
  timestamp: string;
  latency_ms: number;
  operation: string;
}

export function LatencyChart() {
  const [data, setData] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [metricsRes, statsRes] = await Promise.all([
        fetch('/api/v1/monitoring/latency?hours=1'),
        fetch('/api/v1/monitoring/latency/stats?hours=1'),
      ]);

      const metrics = await metricsRes.json();
      const stats = await statsRes.json();

      // Group by timestamp (minute)
      const grouped = metrics.metrics.reduce((acc: any, m: LatencyData) => {
        const minute = new Date(m.timestamp).toISOString().slice(0, 16);
        if (!acc[minute]) {
          acc[minute] = { timestamp: minute, total: 0, count: 0 };
        }
        acc[minute].total += m.latency_ms;
        acc[minute].count += 1;
        return acc;
      }, {});

      const chartData = Object.values(grouped).map((g: any) => ({
        time: new Date(g.timestamp).toLocaleTimeString(),
        latency: Math.round(g.total / g.count),
      }));

      setData(chartData);
      setStats(stats);
    } catch (error) {
      console.error('Failed to fetch latency data:', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg.toFixed(2)}ms</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">P95</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.p95.toFixed(2)}ms</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">P99</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.p99.toFixed(2)}ms</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Max</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.max.toFixed(2)}ms</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Latency Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#8884d8" name="Avg Latency" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
