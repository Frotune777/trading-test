'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { preferencesAPI, QUADWeights } from '@/lib/api/preferences-api';
import { RefreshCw, Save, RotateCcw } from 'lucide-react';

export default function WeightAdjustment() {
  const [weights, setWeights] = useState<QUADWeights | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWeights();
  }, []);

  const loadWeights = async () => {
    try {
      setLoading(true);
      const data = await preferencesAPI.getWeights();
      setWeights(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load weights', err);
      setError('Failed to load weights');
    } finally {
      setLoading(false);
    }
  };

  const handleWeightChange = (pillar: keyof QUADWeights, value: string) => {
    if (!weights) return;
    const numValue = parseFloat(value);
    setWeights({ ...weights, [pillar]: numValue });
  };

  const handleSave = async () => {
    if (!weights) return;

    // Validate sum
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    if (Math.abs(total - 1.0) > 0.01) {
      setError(`Weights must sum to 1.0 (Current: ${total.toFixed(2)})`);
      return;
    }

    try {
      setSaving(true);
      await preferencesAPI.setWeights(weights);
      setError(null);
      alert('Weights saved successfully!');
    } catch (err) {
      console.error('Failed to save weights', err);
      setError('Failed to save weights');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset to default weights?')) return;
    
    try {
      setSaving(true);
      await preferencesAPI.resetWeights();
      await loadWeights();
      alert('Weights reset to default.');
    } catch (err) {
      console.error('Failed to reset weights', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center p-4">Loading preferences...</div>;
  }

  if (!weights) {
    return <div className="text-red-500 p-4">Error loading preferences</div>;
  }

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  const isValid = Math.abs(totalWeight - 1.0) < 0.01;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-bold uppercase tracking-wider">Custom Pillar Weights</CardTitle>
        <div className="flex gap-2">
          <button 
            onClick={handleReset}
            className="p-2 text-muted-foreground hover:text-foreground transition-colors"
            title="Reset to Defaults"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <div className="bg-destructive/10 text-destructive text-xs p-2 rounded">
            {error}
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
          {Object.entries(weights).map(([pillar, weight]) => (
            <div key={pillar} className="space-y-1">
              <div className="flex justify-between text-xs font-semibold uppercase">
                <span>{pillar}</span>
                <span className="font-mono">{weight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weight}
                onChange={(e) => handleWeightChange(pillar as keyof QUADWeights, e.target.value)}
                className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          <div className={`text-xs font-bold font-mono ${isValid ? 'text-success' : 'text-destructive'}`}>
            TOTAL: {totalWeight.toFixed(2)}
          </div>
          <button
            onClick={handleSave}
            disabled={saving || !isValid}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm font-bold text-white transition-all
              ${isValid ? 'bg-primary hover:bg-primary/90' : 'bg-gray-400 cursor-not-allowed'}
            `}
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Configuration
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
