'use client';

import { useState, useEffect } from 'react';
import { FileText, Filter, Download } from 'lucide-react';
import { productionAPI } from '@/lib/api/production-api';
import { AuditLog } from '@/types/production';

const EVENT_TYPES = [
  'ORDER_PLACED',
  'ORDER_FILLED',
  'ORDER_CANCELLED',
  'ORDER_REJECTED',
  'STRATEGY_CREATED',
  'STRATEGY_ACTIVATED',
  'WEBHOOK_RECEIVED',
  'RISK_CHECK_FAILED',
  'RECONCILIATION_RUN',
  'DISCREPANCY_DETECTED',
  'SYSTEM_ERROR'
];

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventType, setEventType] = useState<string>('');
  const [hours, setHours] = useState(24);

  useEffect(() => {
    loadLogs();
  }, [eventType, hours]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const params: any = { hours, limit: 100 };
      if (eventType) params.event_type = eventType;
      
      const data = await productionAPI.queryAuditLogs(params);
      setLogs(data.logs);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileText className="w-8 h-8" />
            Audit Logs
          </h1>
          <p className="text-muted-foreground">Complete audit trail of all system operations</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          className="px-3 py-2 border rounded-lg"
        >
          <option value="">All Events</option>
          {EVENT_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <select
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          className="px-3 py-2 border rounded-lg"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
        </select>
        <button className="ml-auto flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-muted">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Logs Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium">Timestamp</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Event Type</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Symbol</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Action</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Broker</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t hover:bg-muted/30">
                  <td className="px-4 py-2 text-sm">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      log.event_type.includes('ERROR') || log.event_type.includes('REJECTED')
                        ? 'bg-red-100 text-red-800'
                        : log.event_type.includes('FILLED') || log.event_type.includes('ACTIVATED')
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-medium">{log.symbol || '-'}</td>
                  <td className="px-4 py-2">{log.action || '-'}</td>
                  <td className="px-4 py-2 capitalize">{log.broker || '-'}</td>
                  <td className="px-4 py-2 text-sm text-muted-foreground max-w-xs truncate">
                    {log.details ? JSON.stringify(log.details) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {logs.length === 0 && !loading && (
        <div className="text-center py-12 text-muted-foreground">
          No audit logs found for the selected filters
        </div>
      )}
    </div>
  );
}
