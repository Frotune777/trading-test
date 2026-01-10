'use client';

import { useState, useEffect } from 'react';
import { TestTube, Power, PowerOff, RefreshCw, Trash2 } from 'lucide-react';
import { productionAPI } from '@/lib/api/production-api';
import { SandboxPortfolio } from '@/types/production';

export default function SandboxPage() {
  const [portfolio, setPortfolio] = useState<SandboxPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const data = await productionAPI.getSandboxPortfolio();
      setPortfolio(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSandbox = async () => {
    try {
      if (portfolio?.enabled) {
        await productionAPI.disableSandbox();
      } else {
        await productionAPI.enableSandbox();
      }
      await loadPortfolio();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset the sandbox? This will clear all virtual positions and orders.')) {
      return;
    }

    try {
      await productionAPI.resetSandbox();
      await loadPortfolio();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TestTube className="w-8 h-8" />
            Sandbox Mode
          </h1>
          <p className="text-muted-foreground">Paper trading - test strategies without real money</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            disabled={!portfolio?.enabled}
            className="flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            Reset
          </button>
          <button
            onClick={handleToggleSandbox}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              portfolio?.enabled
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {portfolio?.enabled ? (
              <>
                <PowerOff className="w-4 h-4" />
                Disable Sandbox
              </>
            ) : (
              <>
                <Power className="w-4 h-4" />
                Enable Sandbox
              </>
            )}
          </button>
        </div>
      </div>

      {/* Status Banner */}
      {portfolio && (
        <div className={`p-4 rounded-lg border-2 ${
          portfolio.enabled
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-gray-50 border-gray-200 text-gray-800'
        }`}>
          <div className="flex items-center gap-2">
            {portfolio.enabled ? (
              <>
                <Power className="w-5 h-5" />
                <span className="font-semibold">Sandbox Mode ACTIVE</span>
                <span className="ml-2">- All orders will be simulated</span>
              </>
            ) : (
              <>
                <PowerOff className="w-5 h-5" />
                <span className="font-semibold">Sandbox Mode INACTIVE</span>
                <span className="ml-2">- Orders will be placed with real brokers</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Virtual Portfolio */}
      {portfolio && portfolio.enabled && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-muted px-4 py-3 border-b">
            <h2 className="font-semibold">Virtual Portfolio</h2>
          </div>
          {portfolio.positions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium">Symbol</th>
                    <th className="px-4 py-2 text-left text-sm font-medium">Exchange</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">Quantity</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">Avg Price</th>
                    <th className="px-4 py-2 text-right text-sm font-medium">P&L</th>
                    <th className="px-4 py-2 text-left text-sm font-medium">Product</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.positions.map((pos, idx) => (
                    <tr key={idx} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-2 font-medium">{pos.symbol}</td>
                      <td className="px-4 py-2">{pos.exchange}</td>
                      <td className="px-4 py-2 text-right">{pos.quantity}</td>
                      <td className="px-4 py-2 text-right">₹{pos.average_price.toFixed(2)}</td>
                      <td className={`px-4 py-2 text-right font-medium ${
                        pos.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ₹{pos.pnl.toFixed(2)}
                      </td>
                      <td className="px-4 py-2">{pos.product}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              <p>No virtual positions yet</p>
              <p className="text-sm mt-2">Place orders in sandbox mode to see them here</p>
            </div>
          )}
        </div>
      )}

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">How Sandbox Mode Works</h3>
        <ul className="text-sm space-y-1 list-disc list-inside">
          <li>All orders are simulated - no real money involved</li>
          <li>Realistic fills with small slippage (±0.1%)</li>
          <li>Virtual portfolio tracks your positions</li>
          <li>Perfect for testing strategies risk-free</li>
          <li>Reset anytime to start fresh</li>
        </ul>
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
