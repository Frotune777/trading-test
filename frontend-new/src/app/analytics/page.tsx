'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Percent } from 'lucide-react';
import { productionAPI } from '@/lib/api/production-api';
import { BrokerAnalytics } from '@/types/production';

const BROKERS = ['zerodha', 'angelone', 'fyers', 'dhan', 'upstox', 'finvasia'];

export default function AnalyticsPage() {
  const [brokerData, setBrokerData] = useState<Record<string, BrokerAnalytics>>({});
  const [loading, setLoading] = useState(true);
  const [hours, setHours] = useState(24);

  useEffect(() => {
    loadAnalytics();
  }, [hours]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const results = await Promise.all(
        BROKERS.map(broker => 
          productionAPI.getBrokerAnalytics(broker, hours)
            .catch(() => ({ broker, no_data: true } as BrokerAnalytics))
        )
      );
      
      const data = results.reduce((acc, result) => {
        acc[result.broker] = result;
        return acc;
      }, {} as Record<string, BrokerAnalytics>);
      
      setBrokerData(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Execution Analytics</h1>
          <p className="text-muted-foreground">Broker performance and execution quality metrics</p>
        </div>
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="px-4 py-2 border rounded-lg"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
        </select>
      </div>

      {/* Broker Performance Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {BROKERS.map(broker => {
          const data = brokerData[broker];
          if (!data || data.no_data) {
            return (
              <div key={broker} className="border rounded-lg p-4 bg-muted/30">
                <h3 className="font-semibold capitalize mb-2">{broker}</h3>
                <p className="text-sm text-muted-foreground">No data available</p>
              </div>
            );
          }

          return (
            <div key={broker} className="border rounded-lg p-4 space-y-3 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start">
                <h3 className="font-semibold capitalize">{broker}</h3>
                <span className="text-xs text-muted-foreground">{data.total_orders} orders</span>
              </div>

              <div className="space-y-2">
                {/* Latency */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>Avg Latency</span>
                  </div>
                  <span className="font-medium">
                    {data.avg_latency_ms ? `${data.avg_latency_ms.toFixed(0)}ms` : '-'}
                  </span>
                </div>

                {/* Slippage */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Percent className="w-4 h-4" />
                    <span>Avg Slippage</span>
                  </div>
                  <span className={`font-medium ${
                    data.avg_slippage_percent && Math.abs(data.avg_slippage_percent) > 0.1
                      ? 'text-yellow-600'
                      : 'text-green-600'
                  }`}>
                    {data.avg_slippage_percent ? `${data.avg_slippage_percent.toFixed(2)}%` : '-'}
                  </span>
                </div>

                {/* Fill Rate */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <TrendingUp className="w-4 h-4" />
                    <span>Fill Rate</span>
                  </div>
                  <span className="font-medium text-green-600">
                    {data.fill_rate.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Progress Bar for Fill Rate */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all"
                  style={{ width: `${data.fill_rate}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Total Orders</div>
          <div className="text-2xl font-bold">
            {Object.values(brokerData).reduce((sum, b) => sum + (b.total_orders || 0), 0)}
          </div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Avg Latency</div>
          <div className="text-2xl font-bold">
            {(() => {
              const latencies = Object.values(brokerData)
                .filter(b => b.avg_latency_ms)
                .map(b => b.avg_latency_ms!);
              return latencies.length > 0
                ? `${(latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(0)}ms`
                : '-';
            })()}
          </div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Avg Slippage</div>
          <div className="text-2xl font-bold">
            {(() => {
              const slippages = Object.values(brokerData)
                .filter(b => b.avg_slippage_percent)
                .map(b => b.avg_slippage_percent!);
              return slippages.length > 0
                ? `${(slippages.reduce((a, b) => a + b, 0) / slippages.length).toFixed(2)}%`
                : '-';
            })()}
          </div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Overall Fill Rate</div>
          <div className="text-2xl font-bold text-green-600">
            {(() => {
              const fillRates = Object.values(brokerData)
                .filter(b => !b.no_data)
                .map(b => b.fill_rate);
              return fillRates.length > 0
                ? `${(fillRates.reduce((a, b) => a + b, 0) / fillRates.length).toFixed(1)}%`
                : '-';
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}
