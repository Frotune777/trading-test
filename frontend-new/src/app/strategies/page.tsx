'use client';

import { useState, useEffect } from 'react';
import { Plus, RefreshCw, Power, PowerOff, Trash2, Edit, ExternalLink } from 'lucide-react';
import { strategyAPI } from '@/lib/api/strategy-api';
import { Strategy } from '@/types/strategy';

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      const data = await strategyAPI.listStrategies();
      setStrategies(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (id: number) => {
    try {
      await strategyAPI.toggleStrategy(id);
      await loadStrategies();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this strategy?')) return;
    
    try {
      await strategyAPI.deleteStrategy(id);
      await loadStrategies();
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Strategy Management</h1>
          <p className="text-muted-foreground">Manage webhook-based trading strategies</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          <Plus className="w-4 h-4" />
          Create Strategy
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Strategies Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {strategies.map((strategy) => (
          <div
            key={strategy.id}
            className="border rounded-lg p-4 space-y-3 hover:shadow-lg transition-shadow"
          >
            {/* Header */}
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold text-lg">{strategy.name}</h3>
                <p className="text-sm text-muted-foreground">{strategy.platform}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggle(strategy.id)}
                  className={`p-2 rounded ${
                    strategy.is_active
                      ? 'bg-green-100 text-green-600 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  title={strategy.is_active ? 'Active' : 'Inactive'}
                >
                  {strategy.is_active ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => handleDelete(strategy.id)}
                  className="p-2 rounded bg-red-100 text-red-600 hover:bg-red-200"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mode:</span>
                <span className="font-medium">{strategy.trading_mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Type:</span>
                <span className="font-medium">{strategy.is_intraday ? 'Intraday' : 'Positional'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Symbols:</span>
                <span className="font-medium">{strategy.symbol_count}</span>
              </div>
              {strategy.is_intraday && strategy.squareoff_time && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Squareoff:</span>
                  <span className="font-medium">{strategy.squareoff_time}</span>
                </div>
              )}
            </div>

            {/* Webhook URL */}
            <div className="pt-3 border-t">
              <p className="text-xs text-muted-foreground mb-1">Webhook URL:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs bg-muted px-2 py-1 rounded truncate">
                  {strategy.webhook_url}
                </code>
                <button
                  onClick={() => navigator.clipboard.writeText(strategy.webhook_url)}
                  className="p-1 hover:bg-muted rounded"
                  title="Copy"
                >
                  <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Status Badge */}
            <div className="flex gap-2">
              <span
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  strategy.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {strategy.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {strategies.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">No strategies yet</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            <Plus className="w-4 h-4" />
            Create Your First Strategy
          </button>
        </div>
      )}

      {/* Create Form Modal - Placeholder */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <div className="bg-slate-950 border border-slate-800 rounded-lg p-6 max-w-md w-full shadow-2xl">
            <h2 className="text-xl font-bold mb-4">Create Strategy</h2>
            <form onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                try {
                    await strategyAPI.createStrategy({
                        name: formData.get('name') as string,
                        platform: formData.get('platform') as any,
                        is_intraday: formData.get('is_intraday') === 'on',
                        trading_mode: formData.get('trading_mode') as any,
                        description: formData.get('description') as string,
                        squareoff_time: formData.get('squareoff_time') as string || undefined
                    });
                    setShowCreateForm(false);
                    loadStrategies();
                } catch (err: any) {
                    setError(err.message);
                }
            }} className="space-y-4">
                
                {/* Name */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">Strategy Name</label>
                    <input name="name" required className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md" placeholder="e.g., Nifty Trend Following" />
                </div>

                {/* Description */}
                 <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <textarea name="description" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md" placeholder="Brief description..." />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    {/* Platform */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Platform</label>
                        <select name="platform" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md">
                            <option value="TradingView">TradingView</option>
                            <option value="ChartInk">ChartInk</option>
                            <option value="Python">Python</option>
                            <option value="Manual">Manual</option>
                        </select>
                    </div>

                    {/* Mode */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Trading Mode</label>
                        <select name="trading_mode" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md">
                            <option value="BOTH">Both</option>
                            <option value="LONG">Long Only</option>
                            <option value="SHORT">Short Only</option>
                        </select>
                    </div>
                </div>

                {/* Intraday Checkbox */}
                <div className="flex items-center gap-2">
                    <input type="checkbox" name="is_intraday" id="is_intraday" className="h-4 w-4 rounded border-gray-300" />
                    <label htmlFor="is_intraday" className="text-sm">Intraday Strategy</label>
                </div>

                {/* Squareoff Time (Conditional) */}
                <div className="space-y-2">
                    <label className="text-sm font-medium">Square-off Time (IST)</label>
                    <input type="time" name="squareoff_time" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-md" />
                </div>

                <div className="flex gap-3 pt-4">
                    <button type="button" onClick={() => setShowCreateForm(false)} className="flex-1 px-4 py-2 hover:bg-slate-800 rounded-lg">Cancel</button>
                    <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium">Create Strategy</button>
                </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
