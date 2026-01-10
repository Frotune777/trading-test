'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { riskApi, KillSwitchStatus } from '@/lib/api/risk';
import { Power, AlertTriangle, Lock, Unlock, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

interface KillSwitchProps {
    status: KillSwitchStatus;
}

export default function KillSwitch({ status }: KillSwitchProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [reason, setReason] = useState('');
    const [confirmed, setConfirmed] = useState(false);
    const [deactivateReason, setDeactivateReason] = useState('');

    const queryClient = useQueryClient();

    const activateMutation = useMutation({
        mutationFn: riskApi.activateKillSwitch,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['risk-dashboard'] });
            toast.error('KILL SWITCH ACTIVATED - TRADING DISABLED');
            setIsOpen(false);
            resetForm();
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to activate kill switch');
        }
    });

    const deactivateMutation = useMutation({
        mutationFn: riskApi.deactivateKillSwitch,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['risk-dashboard'] });
            toast.success('Kill switch deactivated - Trading enabled');
            setDeactivateReason('');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to deactivate kill switch');
        }
    });

    const resetForm = () => {
        setReason('');
        setConfirmed(false);
    };

    const handleActivate = () => {
        if (!confirmed || reason.length < 10) return;
        activateMutation.mutate({ reason, confirmed });
    };

    if (status.enabled) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-500 rounded-xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Power className="w-32 h-32 text-red-500" />
                </div>

                <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-red-100 dark:bg-red-900/50 rounded-full">
                            <Power className="w-8 h-8 text-red-600 dark:text-red-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-red-700 dark:text-red-400">
                                KILL SWITCH ACTIVE
                            </h2>
                            <p className="text-red-600 dark:text-red-300">
                                All trading operations are currently suspended
                            </p>
                        </div>
                    </div>

                    <div className="bg-white/50 dark:bg-black/20 rounded-lg p-4 mb-6">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Activated by:</span>
                                <p className="font-medium text-gray-900 dark:text-white">
                                    {status.activated_by}
                                </p>
                            </div>
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Time:</span>
                                <p className="font-medium text-gray-900 dark:text-white">
                                    {status.activated_at ? new Date(status.activated_at).toLocaleString() : '-'}
                                </p>
                            </div>
                            <div className="col-span-2">
                                <span className="text-gray-500 dark:text-gray-400">Reason:</span>
                                <p className="font-medium text-gray-900 dark:text-white mt-1">
                                    {status.reason}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <input
                            type="text"
                            value={deactivateReason}
                            onChange={(e) => setDeactivateReason(e.target.value)}
                            placeholder="Enter reason to resume trading..."
                            className="w-full px-4 py-2 rounded-lg border border-red-200 dark:border-red-800 focus:ring-2 focus:ring-red-500 outline-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        />
                        <button
                            onClick={() => deactivateMutation.mutate(deactivateReason)}
                            disabled={deactivateReason.length < 5 || deactivateMutation.isPending}
                            className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            <Unlock className="w-5 h-5" />
                            {deactivateMutation.isPending ? 'Deactivating...' : 'Deactivate Kill Switch'}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <>
            <button
                onClick={() => setIsOpen(true)}
                className="group relative w-full bg-white dark:bg-gray-800 border-2 border-red-100 dark:border-red-900/30 hover:border-red-500 dark:hover:border-red-500 p-6 rounded-xl transition-all duration-300"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-gray-100 dark:bg-gray-700 group-hover:bg-red-100 dark:group-hover:bg-red-900/30 rounded-full transition-colors">
                            <Power className="w-6 h-6 text-gray-400 group-hover:text-red-500 transition-colors" />
                        </div>
                        <div className="text-left">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">
                                Emergency Stop
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Suspend all trading operations
                            </p>
                        </div>
                    </div>
                    <AlertTriangle className="w-5 h-5 text-gray-300 group-hover:text-red-400 transition-colors" />
                </div>
            </button>

            {/* Confirmation Modal */}
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6 border-2 border-red-500 animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                                <AlertTriangle className="w-8 h-8 text-red-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                                    Activate Kill Switch?
                                </h3>
                                <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                                    This will immediately stop ALL trading.
                                </p>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Reason for activation (required)
                                </label>
                                <textarea
                                    value={reason}
                                    onChange={(e) => setReason(e.target.value)}
                                    placeholder="e.g., Extreme market volatility, Data feed latency..."
                                    rows={3}
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 outline-none bg-white dark:bg-gray-900 text-gray-900 dark:text-white resize-none"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Minimum 10 characters required.
                                </p>
                            </div>

                            <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/10 rounded-lg">
                                <input
                                    type="checkbox"
                                    id="confirm-kill"
                                    checked={confirmed}
                                    onChange={(e) => setConfirmed(e.target.checked)}
                                    className="w-5 h-5 text-red-600 focus:ring-red-500 rounded border-gray-300"
                                />
                                <label htmlFor="confirm-kill" className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer">
                                    I understand this action cannot be undone automatically.
                                </label>
                            </div>

                            <div className="flex gap-3 mt-6">
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleActivate}
                                    disabled={!confirmed || reason.length < 10 || activateMutation.isPending}
                                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    <Power className="w-4 h-4" />
                                    {activateMutation.isPending ? 'Activating...' : 'ACTIVATE'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
