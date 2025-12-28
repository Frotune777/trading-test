/**
 * Traffic Chart Component
 * Displays API traffic and error rate metrics
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function TrafficChart() {
  const [endpointData, setEndpointData] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, endpointsRes] = await Promise.all([
        fetch('/api/v1/monitoring/traffic?hours=1'),
        fetch('/api/v1/monitoring/traffic/endpoints?hours=1'),
      ]);

      const stats = await statsRes.json();
      const endpoints = await endpointsRes.json();

      setStats(stats);
      setEndpointData(endpoints.endpoints.slice(0, 10)); // Top 10
    } catch (error) {
      console.error('Failed to fetch traffic data:', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_requests.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats?.error_rate.toFixed(2)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.avg_response_time_ms.toFixed(2)}ms
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top Endpoints by Request Count</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={endpointData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="endpoint" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Endpoint Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {endpointData.map((endpoint, i) => (
              <div key={i} className="flex items-center justify-between border-b pb-2">
                <div>
                  <div className="font-medium">{endpoint.endpoint}</div>
                  <div className="text-sm text-muted-foreground">
                    {endpoint.method}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">{endpoint.count} requests</div>
                  <div className="text-sm text-muted-foreground">
                    {endpoint.avg_response_time_ms.toFixed(2)}ms avg
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
