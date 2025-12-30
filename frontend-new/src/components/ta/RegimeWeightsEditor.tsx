'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Save, RefreshCcw, Info } from 'lucide-react';

interface RegimeWeightsEditorProps {
    regime: string;
    weights: Record<string, number>;
    onSave: (newWeights: Record<string, number>) => Promise<void>;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
const CATEGORIES = ['trend', 'momentum', 'volatility', 'volume'];

const RegimeWeightsEditor: React.FC<RegimeWeightsEditorProps> = ({ regime, weights, onSave }) => {
    const [localWeights, setLocalWeights] = useState<Record<string, number>>(weights);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    useEffect(() => {
        setLocalWeights(weights);
    }, [weights]);

    const handleSliderChange = (category: string, value: number) => {
        const newWeights = { ...localWeights, [category]: value / 100 };

        // Normalize others to keep sum at 1.0
        // Simplified normalization for UI experience
        const otherCategories = CATEGORIES.filter(c => c !== category);
        const remainingWeight = 1.0 - (value / 100);
        const oldOtherSum = otherCategories.reduce((sum, c) => sum + localWeights[c], 0);

        if (oldOtherSum > 0) {
            otherCategories.forEach(c => {
                newWeights[c] = (localWeights[c] / oldOtherSum) * remainingWeight;
            });
        } else {
            // If others were 0, distribute equally
            otherCategories.forEach(c => {
                newWeights[c] = remainingWeight / otherCategories.length;
            });
        }

        setLocalWeights(newWeights);
        setHasChanges(true);
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            await onSave(localWeights);
            setHasChanges(false);
        } finally {
            setSaving(false);
        }
    };

    const chartData = CATEGORIES.map(cat => ({
        name: cat.charAt(0).toUpperCase() + cat.slice(1),
        value: localWeights[cat] * 100
    }));

    return (
        <Card className="bg-slate-950 border-slate-800 flex flex-col">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-bold text-blue-400">
                        {regime.replace('_', ' ')}
                    </CardTitle>
                    <div className="p-1.5 bg-blue-500/10 rounded-full">
                        <Info className="w-4 h-4 text-blue-400" />
                    </div>
                </div>
                <CardDescription>Adjust indicator importance for this regime.</CardDescription>
            </CardHeader>

            <CardContent className="flex-1 space-y-6">
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                <div className="space-y-4">
                    {CATEGORIES.map((cat, idx) => (
                        <div key={cat} className="space-y-1">
                            <div className="flex justify-between text-sm">
                                <span className="capitalize text-slate-400">{cat}</span>
                                <span className="font-mono text-blue-400">{(localWeights[cat] * 100).toFixed(0)}%</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={localWeights[cat] * 100}
                                onChange={(e) => handleSliderChange(cat, parseInt(e.target.value))}
                                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                            />
                        </div>
                    ))}
                </div>
            </CardContent>

            <CardFooter className="pt-4 border-t border-slate-900 flex gap-2">
                <button
                    onClick={() => { setLocalWeights(weights); setHasChanges(false); }}
                    className="flex-1 py-2 text-sm text-slate-400 hover:text-white transition-colors flex items-center justify-center gap-2"
                >
                    <RefreshCcw className="w-4 h-4" />
                    Reset
                </button>
                <button
                    onClick={handleSave}
                    disabled={!hasChanges || saving}
                    className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:grayscale text-white rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2"
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Weights
                </button>
            </CardFooter>
        </Card>
    );
};

const Loader2 = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2V6M12 18V22M6 12H2M22 12H18M18.3636 18.3636L15.5352 15.5352M8.4645 8.4645L5.63607 5.63607M18.3636 5.63607L15.5352 8.46447M8.46447 15.5352L5.63603 18.3636" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export default RegimeWeightsEditor;
