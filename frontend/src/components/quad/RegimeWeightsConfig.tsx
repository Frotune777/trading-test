'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taApi, type TAWeights, type RegimeWeights } from '@/lib/api/ta';
import { MarketRegime } from '../market/RegimeIndicator';
import { Save, RotateCcw, AlertCircle, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

const REGIME_LABELS: Record<string, string> = {
    TRENDING_UP: 'Trending Up',
    TRENDING_DOWN: 'Trending Down',
    RANGING: 'Ranging',
    VOLATILE: 'Volatile',
    UNKNOWN: 'Unknown',
};

export default function RegimeWeightsConfig() {
    const [selectedRegime, setSelectedRegime] = useState<MarketRegime>('TRENDING_UP');
    const [weights, setWeights] = useState<TAWeights>({
        trend: 0.5,
        momentum: 0.3,
        volatility: 0.1,
        volume: 0.1,
    });
    const [hasChanges, setHasChanges] = useState(false);

    const queryClient = useQueryClient();

    // Load all weights
    const { data: allWeights, isLoading } = useQuery<RegimeWeights>({
        queryKey: ['ta-weights'],
        queryFn: () => taApi.getWeights(),
    });

    // Update weights mutation
    const updateMutation = useMutation({
        mutationFn: ({ regime, weights }: { regime: string; weights: TAWeights }) =>
            taApi.updateWeights(regime, weights),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ta-weights'] });
            toast.success('Weights updated successfully');
            setHasChanges(false);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to update weights');
        },
    });

    // Update local weights when regime changes or data loads
    useEffect(() => {
        if (allWeights && allWeights[selectedRegime]) {
            setWeights(allWeights[selectedRegime]);
            setHasChanges(false);
        }
    }, [selectedRegime, allWeights]);

    const handleWeightChange = (category: keyof TAWeights, value: number) => {
        setWeights(prev => ({ ...prev, [category]: value }));
        setHasChanges(true);
    };

    const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);
    const isValid = Math.abs(totalWeight - 1.0) < 0.01;

    const handleSave = () => {
        if (!isValid) {
            toast.error('Weights must sum to 1.0');
            return;
        }
        updateMutation.mutate({ regime: selectedRegime, weights });
    };

    const handleReset = () => {
        if (allWeights && allWeights[selectedRegime]) {
            setWeights(allWeights[selectedRegime]);
            setHasChanges(false);
        }
    };

    if (isLoading) {
        return (
            <div className="w-full h-96 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Loading weights...</p>
            </div>
        );
    }

    return (
        <div className="w-full space-y-6">
            {/* Regime Selector */}
            <div className="flex flex-wrap gap-2">
                {Object.keys(REGIME_LABELS).map((regime) => (
                    <button
                        key={regime}
                        onClick={() => setSelectedRegime(regime as MarketRegime)}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${selectedRegime === regime
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                            }`}
                    >
                        {REGIME_LABELS[regime]}
                    </button>
                ))}
            </div>

            {/* Weights Configuration */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow space-y-6">
                <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Configure Weights for {REGIME_LABELS[selectedRegime]}
                    </h3>
                    <div className="flex items-center gap-2">
                        {isValid ? (
                            <div className="flex items-center gap-1 text-green-600">
                                <CheckCircle2 className="w-4 h-4" />
                                <span className="text-sm">Valid</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1 text-red-600">
                                <AlertCircle className="w-4 h-4" />
                                <span className="text-sm">Sum: {totalWeight.toFixed(2)}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Sliders */}
                <div className="space-y-6">
                    {(Object.keys(weights) as Array<keyof TAWeights>).map((category) => (
                        <div key={category} className="space-y-2">
                            <div className="flex justify-between items-center">
                                <label className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                                    {category}
                                </label>
                                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                                    {weights[category].toFixed(2)}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.01"
                                value={weights[category]}
                                onChange={(e) => handleWeightChange(category, parseFloat(e.target.value))}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-blue-600"
                            />
                            <div className="flex justify-between text-xs text-gray-500">
                                <span>0.00</span>
                                <span>0.50</span>
                                <span>1.00</span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Total Weight Indicator */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Total Weight
                        </span>
                        <span className={`text-lg font-bold ${isValid ? 'text-green-600' : 'text-red-600'}`}>
                            {totalWeight.toFixed(2)}
                        </span>
                    </div>
                    {!isValid && (
                        <p className="text-xs text-red-600 mt-1">
                            Weights must sum to exactly 1.0
                        </p>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                    <button
                        onClick={handleSave}
                        disabled={!hasChanges || !isValid || updateMutation.isPending}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                        <Save className="w-4 h-4" />
                        {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                        onClick={handleReset}
                        disabled={!hasChanges}
                        className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        <RotateCcw className="w-4 h-4" />
                        Reset
                    </button>
                </div>
            </div>
        </div>
    );
}
