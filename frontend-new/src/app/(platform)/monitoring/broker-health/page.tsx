'use client';

import { useState, useEffect } from 'react';
import { Activity, RefreshCw, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { productionAPI } from '@/lib/api/production-api';
import { SystemHealth } from '@/types/production';

export default function BrokerHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    try {
      setLoading(true);
      const data = await productionAPI.getSystemHealth();
      setHealth(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return 'text-green-600 bg-green-100';
      case 'DEGRADED':
        return 'text-yellow-600 bg-yellow-100';
      case 'UNHEALTHY':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return <CheckCircle className="w-5 h-5" />;
      case 'DEGRADED':
        return <AlertTriangle className="w-5 h-5" />;
      case 'UNHEALTHY':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Broker Health Monitor</h1>
          <p className="text-muted-foreground">Real-time system and broker health status</p>
        </div>
        <button
          onClick={loadHealth}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Last Update */}
      <div className="text-sm text-muted-foreground">
        Last updated: {lastUpdate.toLocaleTimeString()}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Overall Status */}
      {health && (
        <div className={`p-6 rounded-lg border-2 ${getStatusColor(health.overall_status)}`}>
          <div className="flex items-center gap-3">
            {getStatusIcon(health.overall_status)}
            <div>
              <h2 className="text-xl font-bold">System Status: {health.overall_status}</h2>
              <p className="text-sm opacity-80">All components monitored</p>
            </div>
          </div>
        </div>
      )}

      {/* Component Health Grid */}
      {health && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(health.components).map(([name, component]) => (
            <div
              key={name}
              className="border rounded-lg p-4 space-y-3 hover:shadow-lg transition-shadow"
            >
              {/* Component Header */}
              <div className="flex items-center justify-between">
                <h3 className="font-semibold capitalize">{name.replace('_', ' ')}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                  {component.status}
                </span>
              </div>

              {/* Component Details */}
              <div className="space-y-2 text-sm">
                {Object.entries(component).map(([key, value]) => {
                  if (key === 'status') return null;
                  return (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}:</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading State */}
      {loading && !health && (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
        </div>
      )}
    </div>
  );
}
