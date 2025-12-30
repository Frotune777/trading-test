'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { strategyApi, type Strategy } from '@/lib/api/strategy';
import { Play, Pause, Edit, Trash2, Copy, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

interface StrategyListProps {
    onEdit?: (strategy: Strategy) => void;
    onViewCode?: (strategy: Strategy) => void;
}

export default function StrategyList({ onEdit, onViewCode }: StrategyListProps) {
    const queryClient = useQueryClient();

    const { data: strategies, isLoading, error } = useQuery<Strategy[]>({
        queryKey: ['strategies'],
        queryFn: () => strategyApi.getStrategies(),
        refetchInterval: 30000,
    });

    const toggleMutation = useMutation({
        mutationFn: (id: number) => strategyApi.toggleStrategy(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
            toast.success('Strategy status updated');
        },
        onError: () => {
            toast.error('Failed to toggle strategy');
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: number) => strategyApi.deleteStrategy(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategies'] });
            toast.success('Strategy deleted');
        },
        onError: () => {
            toast.error('Failed to delete strategy');
        },
    });

    const handleDelete = (id: number, name: string) => {
        if (confirm(`Are you sure you want to delete "${name}"?`)) {
            deleteMutation.mutate(id);
        }
    };

    if (isLoading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-48 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <p className="text-red-600 dark:text-red-400">Failed to load strategies</p>
            </div>
        );
    }

    if (!strategies || strategies.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-600 dark:text-gray-400 mb-4">No strategies found</p>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto">
                    <Plus className="w-4 h-4" />
                    Create Strategy
                </button>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {strategies.map((strategy) => (
                <div
                    key={strategy.id}
                    className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
                >
                    {/* Header */}
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                                {strategy.name}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                                {strategy.description || 'No description'}
                            </p>
                        </div>
                        <button
                            onClick={() => toggleMutation.mutate(strategy.id)}
                            className={`p-2 rounded-lg transition-colors ${strategy.is_active
                                    ? 'bg-green-100 text-green-600 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400'
                                }`}
                            title={strategy.is_active ? 'Active' : 'Inactive'}
                        >
                            {strategy.is_active ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        </button>
                    </div>

                    {/* Type Badge */}
                    <div className="mb-4">
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${strategy.type === 'technical'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                                : strategy.type === 'fundamental'
                                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                                    : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            }`}>
                            {strategy.type}
                        </span>
                        <span className="ml-2 text-xs text-gray-500">
                            {strategy.platform}
                        </span>
                    </div>

                    {/* Metadata */}
                    <div className="mb-4 text-xs text-gray-500 space-y-1">
                        <p>Created: {new Date(strategy.created_at).toLocaleDateString()}</p>
                        <p>Updated: {new Date(strategy.updated_at).toLocaleDateString()}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <button
                            onClick={() => onViewCode?.(strategy)}
                            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                        >
                            <Edit className="w-4 h-4" />
                            Code
                        </button>
                        <button
                            onClick={() => onEdit?.(strategy)}
                            className="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
                            title="Edit"
                        >
                            <Edit className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => handleDelete(strategy.id, strategy.name)}
                            className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50"
                            title="Delete"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
