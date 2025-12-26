'use client';

import { useEffect, useState } from 'react';
import { quadAnalyticsAPI, QUADAlert, CreateAlertRequest } from '@/lib/api/quad-analytics-api';
import { Bell, Plus, Trash2, Check, Activity } from 'lucide-react';

interface AlertManagerProps {
  symbol: string;
}

export default function AlertManager({ symbol }: AlertManagerProps) {
  const [alerts, setAlerts] = useState<QUADAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlert, setNewAlert] = useState<CreateAlertRequest>({
    symbol,
    alert_type: 'CONVICTION_ABOVE',
    threshold: 75,
    channels: ['websocket']
  });

  useEffect(() => {
    loadAlerts();
  }, [symbol]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await quadAnalyticsAPI.listAlerts({ symbol, active_only: true });
      setAlerts(data);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async () => {
    try {
      await quadAnalyticsAPI.createAlert(newAlert);
      setShowCreateForm(false);
      setNewAlert({
        symbol,
        alert_type: 'CONVICTION_ABOVE',
        threshold: 75,
        channels: ['websocket']
      });
      loadAlerts();
    } catch (error) {
      console.error('Error creating alert:', error);
    }
  };

  const handleDeleteAlert = async (alertId: number) => {
    try {
      await quadAnalyticsAPI.deleteAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await quadAnalyticsAPI.acknowledgeAlert(alertId);
      loadAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Bell className="w-5 h-5" />
            QUAD Alerts
          </h3>
          <p className="text-sm text-muted-foreground">
            Monitor conviction thresholds and pillar changes
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Alert
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-gray-50 border rounded-lg p-4 space-y-4">
          <h4 className="font-semibold">Create New Alert</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Alert Type</label>
              <select
                value={newAlert.alert_type}
                onChange={(e) => setNewAlert({ ...newAlert, alert_type: e.target.value as any })}
                className="w-full border rounded px-3 py-2"
              >
                <option value="CONVICTION_ABOVE">Conviction Above</option>
                <option value="CONVICTION_BELOW">Conviction Below</option>
                <option value="PILLAR_DRIFT">Pillar Drift</option>
                <option value="SIGNAL_CHANGE">Signal Change</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Threshold</label>
              <input
                type="number"
                value={newAlert.threshold || 0}
                onChange={(e) => setNewAlert({ ...newAlert, threshold: parseInt(e.target.value) })}
                className="w-full border rounded px-3 py-2"
                min="0"
                max="100"
              />
            </div>
          </div>

          {newAlert.alert_type === 'PILLAR_DRIFT' && (
            <div>
              <label className="block text-sm font-medium mb-1">Pillar</label>
              <select
                value={newAlert.pillar_name || ''}
                onChange={(e) => setNewAlert({ ...newAlert, pillar_name: e.target.value })}
                className="w-full border rounded px-3 py-2"
              >
                <option value="">Select Pillar</option>
                <option value="trend">Trend</option>
                <option value="momentum">Momentum</option>
                <option value="volatility">Volatility</option>
                <option value="liquidity">Liquidity</option>
                <option value="sentiment">Sentiment</option>
                <option value="regime">Regime</option>
              </select>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleCreateAlert}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Create Alert
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Alerts List */}
      <div className="space-y-2">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No active alerts</p>
            <p className="text-sm mt-1">Create an alert to get notified</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border rounded-lg p-4 ${
                alert.triggered_at ? 'bg-yellow-50 border-yellow-300' : 'bg-white'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{alert.alert_type.replace(/_/g, ' ')}</span>
                    {alert.triggered_at && (
                      <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                        TRIGGERED
                      </span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-600 mt-1">
                    {alert.threshold && <span>Threshold: {alert.threshold}</span>}
                    {alert.pillar_name && <span> | Pillar: {alert.pillar_name}</span>}
                  </div>

                  {alert.message && (
                    <div className="text-sm mt-2 text-gray-700">
                      {alert.message}
                    </div>
                  )}

                  {alert.triggered_at && (
                    <div className="text-xs text-gray-500 mt-1">
                      Triggered: {new Date(alert.triggered_at).toLocaleString()}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {alert.triggered_at && (
                    <button
                      onClick={() => handleAcknowledgeAlert(alert.id)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded"
                      title="Acknowledge"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteAlert(alert.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
