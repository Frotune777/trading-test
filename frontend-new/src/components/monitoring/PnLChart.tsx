/**
 * P&L Chart Component
 * Displays real-time P&L with historical chart
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

export function PnLChart() {
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [current, setCurrent] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const userId = 1; // TODO: Get from auth
      const [currentRes, historyRes, performanceRes] = await Promise.all([
        fetch(`/api/v1/monitoring/pnl/${userId}`),
        fetch(`/api/v1/monitoring/pnl/${userId}/history?hours=24`),
        fetch(`/api/v1/monitoring/pnl/${userId}/performance?days=30`),
      ]);

      const current = await currentRes.json();
      const history = await historyRes.json();
      const performance = await performanceRes.json();

      setCurrent(current);
      setPerformance(performance);

      // Format history data
      const chartData = history.snapshots.map((s: any) => ({
        time: new Date(s.timestamp).toLocaleTimeString(),
        total_pnl: s.total_pnl,
        realized_pnl: s.realized_pnl,
        unrealized_pnl: s.unrealized_pnl,
      }));

      setHistoryData(chartData);
    } catch (error) {
      console.error('Failed to fetch P&L data:', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${(current?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
            >
              ₹{current?.total_pnl.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Day P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${(current?.day_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
            >
              ₹{current?.day_pnl.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performance?.win_rate?.toFixed(1) ?? '0.0'}%
            </div>
            <p className="text-xs text-muted-foreground">
              {performance?.winning_trades}/{performance?.total_trades} trades
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${(performance?.avg_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
            >
              ₹{performance?.avg_pnl?.toFixed(2) ?? '0.00'}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>P&L Over Time (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={historyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="total_pnl"
                stroke="#8884d8"
                fill="#8884d8"
                fillOpacity={0.6}
                name="Total P&L"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trade Performance (30 days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <div className="text-sm text-muted-foreground">Total Trades</div>
              <div className="text-2xl font-bold">{performance?.total_trades}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Best Trade</div>
              <div className="text-2xl font-bold text-green-600">
                ₹{performance?.best_trade?.toFixed(2) ?? '0.00'}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Worst Trade</div>
              <div className="text-2xl font-bold text-red-600">
                ₹{performance?.worst_trade?.toFixed(2) ?? '0.00'}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Avg Holding Time</div>
              <div className="text-2xl font-bold">
                {performance?.avg_holding_time_minutes?.toFixed(0) ?? '0'} min
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
