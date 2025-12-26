'use client';

import { useState, useEffect } from 'react';
import { Shield, Bell, RefreshCw } from 'lucide-react';
import { productionAPI } from '@/lib/api/production-api';
import { SystemHealth } from '@/types/production';

export default function MonitoringPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [healthData, metricsData] = await Promise.all([
        productionAPI.getSystemHealth(),
        productionAPI.getSystemMetrics()
      ]);
      setHealth(healthData);
      setMetrics(metricsData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="w-8 h-8" />
            System Monitoring
          </h1>
          <p className="text-muted-foreground">Real-time system health and alerts</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {health && (
        <div className={`p-6 rounded-lg border-2 ${
          health.overall_status === 'HEALTHY' ? 'bg-green-50 border-green-200' :
          health.overall_status === 'DEGRADED' ? 'bg-yellow-50 border-yellow-200' :
          'bg-red-50 border-red-200'
        }`}>
          <h2 className="text-2xl font-bold">
            System Status: {health.overall_status}
          </h2>
          <p className="text-sm mt-1">Last checked: {new Date(health.timestamp).toLocaleString()}</p>
        </div>
      )}

      {metrics && metrics.recent_alerts && metrics.recent_alerts.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-muted px-4 py-3 border-b flex items-center gap-2">
            <Bell className="w-5 h-5" />
            <h2 className="font-semibold">Recent Alerts</h2>
          </div>
          <div className="divide-y">
            {metrics.recent_alerts.map((alert: any, idx: number) => (
              <div key={idx} className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium">{alert.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    alert.level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                    alert.level === 'ERROR' ? 'bg-orange-100 text-orange-800' :
                    alert.level === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.level}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">Monitoring Features</h3>
        <ul className="text-sm space-y-1 list-disc list-inside">
          <li>Real-time system health checks</li>
          <li>Broker connectivity monitoring</li>
          <li>Order queue depth tracking</li>
          <li>Multi-channel alerts (Telegram, Email, WebSocket)</li>
          <li>Automatic failover detection</li>
        </ul>
      </div>
    </div>
  );
}
