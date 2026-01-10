'use client';

import { useState, useEffect } from 'react';
import { Play, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { reconciliationAPI } from '@/lib/api/reconciliation-api';
import { ReconciliationRun, Discrepancy } from '@/types/reconciliation';

export default function ReconciliationPage() {
  const [runs, setRuns] = useState<ReconciliationRun[]>([]);
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [runsData, discData] = await Promise.all([
        reconciliationAPI.listRuns(10),
        reconciliationAPI.listDiscrepancies(24, false) // Unresolved only
      ]);
      setRuns(runsData);
      setDiscrepancies(discData);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerReconciliation = async () => {
    try {
      setRunning(true);
      await reconciliationAPI.triggerReconciliation();
      setTimeout(loadData, 2000); // Reload after 2 seconds
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const handleResolveDiscrepancy = async (id: number) => {
    const action = prompt('Enter resolution action:');
    if (!action) return;

    try {
      await reconciliationAPI.resolveDiscrepancy(id, action);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Position Reconciliation</h1>
          <p className="text-muted-foreground">Auto-sync positions with brokers every 5 minutes</p>
        </div>
        <button
          onClick={handleTriggerReconciliation}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
        >
          <Play className={`w-4 h-4 ${running ? 'animate-pulse' : ''}`} />
          {running ? 'Running...' : 'Run Now'}
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Unresolved Discrepancies Alert */}
      {discrepancies.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span className="font-medium">{discrepancies.length} unresolved discrepancies found</span>
        </div>
      )}

      {/* Discrepancies Table */}
      {discrepancies.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-muted px-4 py-3 border-b">
            <h2 className="font-semibold">Unresolved Discrepancies</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium">Symbol</th>
                  <th className="px-4 py-2 text-left text-sm font-medium">Broker</th>
                  <th className="px-4 py-2 text-right text-sm font-medium">Local Qty</th>
                  <th className="px-4 py-2 text-right text-sm font-medium">Broker Qty</th>
                  <th className="px-4 py-2 text-right text-sm font-medium">Difference</th>
                  <th className="px-4 py-2 text-left text-sm font-medium">Detected</th>
                  <th className="px-4 py-2 text-center text-sm font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {discrepancies.map((disc) => (
                  <tr key={disc.id} className="border-t hover:bg-muted/30">
                    <td className="px-4 py-2 font-medium">{disc.symbol}</td>
                    <td className="px-4 py-2">{disc.broker}</td>
                    <td className="px-4 py-2 text-right">{disc.local_quantity ?? '-'}</td>
                    <td className="px-4 py-2 text-right">{disc.broker_quantity ?? '-'}</td>
                    <td className={`px-4 py-2 text-right font-medium ${disc.difference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {disc.difference > 0 ? '+' : ''}{disc.difference}
                    </td>
                    <td className="px-4 py-2 text-sm text-muted-foreground">
                      {new Date(disc.detected_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <button
                        onClick={() => handleResolveDiscrepancy(disc.id)}
                        className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
                      >
                        Resolve
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reconciliation Runs History */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-muted px-4 py-3 border-b">
          <h2 className="font-semibold">Recent Reconciliation Runs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium">Run Time</th>
                <th className="px-4 py-2 text-left text-sm font-medium">Brokers</th>
                <th className="px-4 py-2 text-right text-sm font-medium">Positions</th>
                <th className="px-4 py-2 text-right text-sm font-medium">Discrepancies</th>
                <th className="px-4 py-2 text-right text-sm font-medium">Duration</th>
                <th className="px-4 py-2 text-center text-sm font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-t hover:bg-muted/30">
                  <td className="px-4 py-2">
                    {new Date(run.run_time).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-sm">{run.brokers_checked.join(', ')}</span>
                  </td>
                  <td className="px-4 py-2 text-right">{run.total_positions}</td>
                  <td className="px-4 py-2 text-right">
                    {run.discrepancies_found > 0 ? (
                      <span className="text-yellow-600 font-medium">{run.discrepancies_found}</span>
                    ) : (
                      <span className="text-green-600">0</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right text-sm text-muted-foreground">
                    {run.duration_ms ? `${run.duration_ms}ms` : '-'}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      run.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      run.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {run.status === 'COMPLETED' && <CheckCircle className="w-3 h-3" />}
                      {run.status === 'RUNNING' && <Clock className="w-3 h-3 animate-spin" />}
                      {run.status === 'FAILED' && <AlertCircle className="w-3 h-3" />}
                      {run.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
        </div>
      )}
    </div>
  );
}
