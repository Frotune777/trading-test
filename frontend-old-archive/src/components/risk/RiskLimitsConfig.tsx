'use client';

import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { riskApi, RiskLimits } from '@/lib/api/risk';
import { Save, RotateCcw, AlertCircle, Shield } from 'lucide-react';
import toast from 'react-hot-toast';

interface RiskLimitsConfigProps {
    initialLimits: RiskLimits;
}

export default function RiskLimitsConfig({ initialLimits }: RiskLimitsConfigProps) {
    const [limits, setLimits] = useState<RiskLimits>(initialLimits);
    const [isDirty, setIsDirty] = useState(false);
    const queryClient = useQueryClient();

    // Reset local state when props change (e.g. after refresh)
    useEffect(() => {
        setLimits(initialLimits);
        setIsDirty(false);
    }, [initialLimits]);

    const updateMutation = useMutation({
        mutationFn: riskApi.updateLimits,
        onSuccess: (newLimits) => {
            queryClient.setQueryData(['risk-dashboard'], (old: any) => ({
                ...old,
                limits: newLimits
            }));
            toast.success('Risk limits updated successfully');
            setLimits(newLimits);
            setIsDirty(false);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to update limits');
        }
    });

    const handleChange = (field: keyof RiskLimits, value: string) => {
        const numValue = parseFloat(value);
        if (isNaN(numValue)) return;

        setLimits(prev => ({
            ...prev,
            [field]: numValue
        }));
        setIsDirty(true);
    };

    const handleReset = () => {
        setLimits(initialLimits);
        setIsDirty(false);
    };

    const handleSave = () => {
        updateMutation.mutate(limits);
    };

    const InputField = ({
        label,
        field,
        min = 0,
        max,
        step = 1,
        prefix = '',
        suffix = ''
    }: {
        label: string,
        field: keyof RiskLimits,
        min?: number,
        max?: number,
        step?: number,
        prefix?: string,
        suffix?: string
    }) => (
        <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {label}
            </label>
            <div className="relative">
                {prefix && (
                    <span className="absolute left-3 top-2 text-gray-400">
                        {prefix}
                    </span>
                )}
                <input
                    type="number"
                    value={limits[field]}
                    onChange={(e) => handleChange(field, e.target.value)}
                    min={min}
                    max={max}
                    step={step}
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 outline-none dark:bg-gray-800 dark:text-white transition-all
            ${prefix ? 'pl-8' : ''} ${suffix ? 'pr-8' : ''}
            ${limits[field] !== initialLimits[field]
                            ? 'border-blue-400 ring-blue-100 bg-blue-50 dark:bg-blue-900/10'
                            : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
                        }
          `}
                />
                {suffix && (
                    <span className="absolute right-3 top-2 text-gray-400">
                        {suffix}
                    </span>
                )}
            </div>
            {limits[field] !== initialLimits[field] && (
                <p className="text-xs text-blue-600 dark:text-blue-400">
                    Changed from {initialLimits[field]}
                </p>
            )}
        </div>
    );

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <div>
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Shield className="w-5 h-5 text-blue-600" />
                        Risk Limits Configuration
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Define system-wide trading constraints
                    </p>
                </div>

                {isDirty && (
                    <div className="flex gap-2 animate-in fade-in slide-in-from-right-4 duration-300">
                        <button
                            onClick={handleReset}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 rounded-lg flex items-center gap-2"
                        >
                            <RotateCcw className="w-4 h-4" />
                            Reset
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={updateMutation.isPending}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium shadow-sm flex items-center gap-2"
                        >
                            <Save className="w-4 h-4" />
                            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                )}
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-6">
                {/* Position Constraints */}
                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider border-b border-gray-100 dark:border-gray-700 pb-2">
                        Position Constraints
                    </h3>
                    <InputField
                        label="Max Open Positions"
                        field="max_positions"
                        max={20}
                    />
                    <InputField
                        label="Max Single Position Size"
                        field="max_position_size"
                        prefix="₹"
                        step={1000}
                    />
                    <InputField
                        label="Max Portfolio Value"
                        field="max_portfolio_value"
                        prefix="₹"
                        step={10000}
                    />
                </div>

                {/* Loss Limits */}
                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider border-b border-gray-100 dark:border-gray-700 pb-2">
                        Loss Limits
                    </h3>
                    <InputField
                        label="Max Daily Loss"
                        field="max_daily_loss"
                        prefix="₹"
                        step={1000}
                    />
                    <InputField
                        label="Max Weekly Loss"
                        field="max_weekly_loss"
                        prefix="₹"
                        step={5000}
                    />
                    <InputField
                        label="Max Drawdown"
                        field="max_drawdown_pct"
                        suffix="%"
                        max={50}
                    />
                </div>

                {/* Concentration Limits */}
                <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider border-b border-gray-100 dark:border-gray-700 pb-2">
                        Concentration Limits
                    </h3>
                    <InputField
                        label="Max Sector Concentration"
                        field="max_sector_concentration_pct"
                        suffix="%"
                        max={100}
                    />
                    <InputField
                        label="Max Single Stock"
                        field="max_single_stock_pct"
                        suffix="%"
                        max={100}
                    />
                </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/10 p-4 border-t border-blue-100 dark:border-blue-900/20 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                <p className="text-sm text-blue-800 dark:text-blue-300">
                    Changes to risk limits take effect immediately for new orders. Existing positions
                    will not be force-closed unless the Kill Switch is activated or stop-losses are hit.
                </p>
            </div>
        </div>
    );
}
