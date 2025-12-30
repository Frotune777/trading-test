'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Database, RefreshCw, Download, AlertCircle } from 'lucide-react';
import MainLayout from '@/components/layout/main-layout';
import { api } from '@/lib/api';

interface Stock {
    symbol: string;
    name?: string;
}

interface DataAvailability {
    symbol: string;
    available: boolean;
    last_update?: string;
    record_count?: number;
    date_range?: {
        from: string;
        to: string;
    };
}

export default function DataSourcePage() {
    const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
    const [symbolInput, setSymbolInput] = useState('');
    const [startDate, setStartDate] = useState(() => {
        const date = new Date();
        date.setMonth(date.getMonth() - 1); // 1 month ago
        return date.toISOString().split('T')[0];
    });
    const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
    const [interval, setInterval] = useState('1d');

    const queryClient = useQueryClient();

    // Fetch available stocks
    const { data: stocksData, isLoading: stocksLoading } = useQuery({
        queryKey: ['stocks'],
        queryFn: async () => {
            const response = await api.get('/data/stocks');
            return response.data;
        },
    });

    // Data ingestion mutation
    const ingestMutation = useMutation({
        mutationFn: async () => {
            const promises = selectedSymbols.map(symbol =>
                api.post('/data/ingest', null, {
                    params: {
                        symbol,
                        start_date: startDate,
                        end_date: endDate,
                        source: 'nse',
                        timeframe: interval,
                    },
                })
            );
            return Promise.all(promises);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['data-availability'] });
            alert('✅ Data ingestion completed successfully!');
        },
        onError: (error: any) => {
            alert(`❌ Data ingestion failed: ${error.message}`);
        },
    });

    // Fetch data availability for selected symbols
    const { data: availabilityData } = useQuery({
        queryKey: ['data-availability', selectedSymbols],
        queryFn: async () => {
            if (selectedSymbols.length === 0) return [];
            const promises = selectedSymbols.map(async (symbol) => {
                try {
                    const response = await api.get(`/data/availability/${symbol}`);
                    return response.data;
                } catch (error) {
                    return {
                        symbol,
                        available: false,
                        error: 'Failed to fetch availability',
                    };
                }
            });
            return Promise.all(promises);
        },
        enabled: selectedSymbols.length > 0,
    });

    const handleAddSymbol = () => {
        const symbol = symbolInput.trim().toUpperCase();
        if (symbol && !selectedSymbols.includes(symbol)) {
            setSelectedSymbols([...selectedSymbols, symbol]);
            setSymbolInput('');
        }
    };

    const handleRemoveSymbol = (symbol: string) => {
        setSelectedSymbols(selectedSymbols.filter(s => s !== symbol));
    };

    const handleIngest = () => {
        if (selectedSymbols.length === 0) {
            alert('Please select at least one symbol');
            return;
        }
        if (confirm(`Ingest data for ${selectedSymbols.length} symbol(s)?`)) {
            ingestMutation.mutate();
        }
    };

    return (
        <MainLayout>
            <div className="p-6 max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Database className="w-8 h-8" />
                        Data Source Configuration
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Configure and ingest NSE market data for analysis
                    </p>
                </div>

                {/* Info Banner */}
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800 dark:text-blue-200">
                        <p className="font-semibold">NSE Data Source</p>
                        <p className="mt-1">
                            This page allows you to manually ingest historical market data from NSE.
                            Data will be stored locally and used for QUAD analysis and backtesting.
                        </p>
                    </div>
                </div>

                {/* Symbol Selection */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                    <h2 className="text-xl font-semibold">Select Symbols</h2>

                    <div className="flex gap-2">
                        <Input
                            placeholder="Enter symbol (e.g., RELIANCE, TCS)"
                            value={symbolInput}
                            onChange={(e) => setSymbolInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                            className="flex-1"
                        />
                        <Button onClick={handleAddSymbol}>Add Symbol</Button>
                    </div>

                    {selectedSymbols.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {selectedSymbols.map(symbol => (
                                <div
                                    key={symbol}
                                    className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full flex items-center gap-2"
                                >
                                    <span className="font-medium">{symbol}</span>
                                    <button
                                        onClick={() => handleRemoveSymbol(symbol)}
                                        className="hover:text-red-600"
                                    >
                                        ×
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Date Range & Interval */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                    <h2 className="text-xl font-semibold">Data Parameters</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Start Date</label>
                            <Input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">End Date</label>
                            <Input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">Interval</label>
                            <Select value={interval} onValueChange={setInterval}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="1d">Daily (1d)</SelectItem>
                                    <SelectItem value="1h">Hourly (1h)</SelectItem>
                                    <SelectItem value="15m">15 Minutes</SelectItem>
                                    <SelectItem value="5m">5 Minutes</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <Button
                        onClick={handleIngest}
                        disabled={ingestMutation.isPending || selectedSymbols.length === 0}
                        className="w-full"
                    >
                        <RefreshCw className={`w-4 h-4 mr-2 ${ingestMutation.isPending ? 'animate-spin' : ''}`} />
                        {ingestMutation.isPending ? 'Ingesting Data...' : 'Ingest Data'}
                    </Button>
                </div>

                {/* Data Availability Table */}
                {availabilityData && availabilityData.length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                        <h2 className="text-xl font-semibold">Data Availability</h2>

                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="border-b border-gray-200 dark:border-gray-700">
                                    <tr>
                                        <th className="text-left py-3 px-4">Symbol</th>
                                        <th className="text-left py-3 px-4">Status</th>
                                        <th className="text-left py-3 px-4">Last Update</th>
                                        <th className="text-left py-3 px-4">Records</th>
                                        <th className="text-left py-3 px-4">Date Range</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {availabilityData.map((item: DataAvailability) => (
                                        <tr key={item.symbol} className="border-b border-gray-100 dark:border-gray-800">
                                            <td className="py-3 px-4 font-medium">{item.symbol}</td>
                                            <td className="py-3 px-4">
                                                {item.available ? (
                                                    <span className="text-green-600 dark:text-green-400">✓ Available</span>
                                                ) : (
                                                    <span className="text-red-600 dark:text-red-400">✗ Not Available</span>
                                                )}
                                            </td>
                                            <td className="py-3 px-4">
                                                {item.last_update ? new Date(item.last_update).toLocaleString() : 'N/A'}
                                            </td>
                                            <td className="py-3 px-4">{item.record_count || 0}</td>
                                            <td className="py-3 px-4">
                                                {item.date_range ? `${item.date_range.from} → ${item.date_range.to}` : 'N/A'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}
