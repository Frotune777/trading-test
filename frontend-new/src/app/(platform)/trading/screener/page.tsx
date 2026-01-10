'use client';

import React, { useState, useEffect } from 'react';
import {
    Search,
    Activity,
    List,
    Download,
    RefreshCcw,
    Play,
    History,
    Settings2,
    AlertCircle,
    FileText,
    Filter
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';

export default function ScreenerPage() {
    const [activeTab, setActiveTab] = useState('scan');
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanTaskId, setScanTaskId] = useState<string | null>(null);
    const [scanStatus, setScanStatus] = useState<string>('Idle');
    const [results, setResults] = useState<any[]>([]);
    const [customLists, setCustomLists] = useState<any[]>([]);
    const [selectedList, setSelectedList] = useState<string>('all');
    const [selectedStrategy, setSelectedStrategy] = useState<string>('9');
    const [selectedIndex, setSelectedIndex] = useState<string>('12');
    const { toast } = useToast();

    const strategies = [
        { id: '1', name: 'Price Reversal' },
        { id: '2', name: 'Breakout Patterns' },
        { id: '9', name: 'Volume Shockers' },
        { id: '10', name: 'Keltner Channel Breakout' },
        { id: '23', name: 'Intraday Momentum' },
    ];

    const indices = [
        { id: '12', name: 'Nifty 50' },
        { id: '13', name: 'Nifty Bank' },
        { id: '14', name: 'Nifty IT' },
        { id: '7', name: 'Nifty Next 50' },
        { id: '28', name: 'F&O Stocks' },
    ];

    const handleStartScan = async () => {
        setIsScanning(true);
        setScanProgress(10);
        setScanStatus('Initializing...');

        try {
            // API Call to trigger scan
            const response = await fetch('/api/v1/screener/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index: selectedIndex,
                    strategy: selectedStrategy,
                    custom_list_id: selectedList === 'all' ? null : parseInt(selectedList)
                })
            });

            if (!response.ok) throw new Error('Failed to start scan');

            const data = await response.json();
            setScanTaskId(data.task_id);

            // Start polling for status
            pollScanStatus(data.task_id);

        } catch (error: any) {
            toast({
                variant: "destructive",
                title: "Scan Error",
                description: error.message || "Failed to start technical scan",
            });
            setIsScanning(false);
        }
    };

    const pollScanStatus = async (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/screener/status/${taskId}`);
                const data = await response.json();

                setScanStatus(data.message || 'Scanning...');
                setScanProgress(data.progress);

                if (data.state === 'SUCCESS') {
                    clearInterval(interval);
                    setIsScanning(false);
                    setScanProgress(100);
                    fetchResults(taskId);
                    toast({
                        title: "Scan Complete",
                        description: "PKScreener finished scanning successfully.",
                    });
                } else if (data.state === 'FAILURE') {
                    clearInterval(interval);
                    setIsScanning(false);
                    toast({
                        variant: "destructive",
                        title: "Scan Failed",
                        description: data.message || "An error occurred during scanning.",
                    });
                }
            } catch (error) {
                clearInterval(interval);
                setIsScanning(false);
            }
        }, 2000);
    };

    const fetchResults = async (taskId: string) => {
        try {
            const response = await fetch(`/api/v1/screener/results/${taskId}`);
            const data = await response.json();
            setResults(data.results);
        } catch (error) {
            console.error('Error fetching results:', error);
        }
    };

    const downloadCSV = () => {
        if (results.length === 0) return;

        const headers = Object.keys(results[0]).join(',');
        const rows = results.map(row =>
            Object.values(row).map(val => `"${val}"`).join(',')
        ).join('\n');

        const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + rows;
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `pkscreener_results_${new Date().toISOString()}.csv`);
        document.body.appendChild(link);
        link.click();
    };

    return (
        <div className="flex flex-col gap-6 p-6 min-h-screen bg-background text-foreground">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">PKScreener</h1>
                    <p className="text-muted-foreground">Advanced Technical Scanning and Pattern Discovery</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                        <Settings2 className="w-4 h-4 mr-2" />
                        Config
                    </Button>
                    <Button variant="outline" size="sm">
                        <History className="w-4 h-4 mr-2" />
                        History
                    </Button>
                </div>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 md:w-[400px]">
                    <TabsTrigger value="scan">
                        <Search className="w-4 h-4 mr-2" />
                        New Scan
                    </TabsTrigger>
                    <TabsTrigger value="results">
                        <List className="w-4 h-4 mr-2" />
                        Results
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="scan" className="mt-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card className="col-span-1 border-primary/20 bg-primary/5">
                            <CardHeader>
                                <CardTitle className="text-lg">Scan Parameters</CardTitle>
                                <CardDescription>Configure your technical scan</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Index / Universe</label>
                                    <Select value={selectedIndex} onValueChange={setSelectedIndex}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select Index" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {indices.map(idx => (
                                                <SelectItem key={idx.id} value={idx.id}>{idx.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Strategy</label>
                                    <Select value={selectedStrategy} onValueChange={setSelectedStrategy}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select Strategy" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {strategies.map(st => (
                                                <SelectItem key={st.id} value={st.id}>{st.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Custom Stock List (Optional)</label>
                                    <Select value={selectedList} onValueChange={setSelectedList}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select List" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">None (Scan Index)</SelectItem>
                                            {customLists.map(list => (
                                                <SelectItem key={list.id} value={list.id.toString()}>{list.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <Button
                                    className="w-full mt-4"
                                    onClick={handleStartScan}
                                    disabled={isScanning}
                                >
                                    {isScanning ? (
                                        <RefreshCcw className="w-4 h-4 mr-2 animate-spin" />
                                    ) : (
                                        <Play className="w-4 h-4 mr-2" />
                                    )}
                                    {isScanning ? 'Scanning...' : 'Execute Scan'}
                                </Button>
                            </CardContent>
                        </Card>

                        <Card className="col-span-1 md:col-span-2">
                            <CardHeader>
                                <CardTitle className="text-lg">Scan Status</CardTitle>
                                <CardDescription>Real-time progress of the active scanner</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-8 flex flex-col justify-center min-h-[200px]">
                                {!isScanning && results.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center text-muted-foreground py-8">
                                        <Activity className="w-12 h-12 mb-4 opacity-20" />
                                        <p>No active scan is currently running.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        <div className="flex justify-between items-end">
                                            <div className="space-y-1">
                                                <p className="text-sm font-medium">Current State: <Badge variant="outline" className="ml-2">{scanStatus}</Badge></p>
                                                <p className="text-xs text-muted-foreground">{scanTaskId ? `Task: ${scanTaskId}` : ''}</p>
                                            </div>
                                            <p className="text-2xl font-bold">{Math.round(scanProgress)}%</p>
                                        </div>
                                        <Progress value={scanProgress} className="h-2" />
                                        <div className="grid grid-cols-4 gap-4">
                                            {[10, 40, 70, 100].map(step => (
                                                <div key={step} className="flex flex-col items-center gap-2">
                                                    <div className={`w-3 h-3 rounded-full ${scanProgress >= step ? 'bg-primary' : 'bg-muted'}`} />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="results" className="mt-6">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0">
                            <div>
                                <CardTitle>Scan Results</CardTitle>
                                <CardDescription>Filtered findings from PKScreener</CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" size="icon" disabled={results.length === 0} onClick={() => setResults([])}>
                                    <RefreshCcw className="w-4 h-4" />
                                </Button>
                                <Button variant="outline" disabled={results.length === 0} onClick={downloadCSV}>
                                    <Download className="w-4 h-4 mr-2" />
                                    Export CSV
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {results.length > 0 ? (
                                <div className="rounded-md border overflow-hidden">
                                    <Table>
                                        <TableHeader className="bg-muted/50">
                                            <TableRow>
                                                {Object.keys(results[0]).map(key => (
                                                    <TableHead key={key} className="font-bold">{key.toUpperCase()}</TableHead>
                                                ))}
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {results.map((row, i) => (
                                                <TableRow key={i} className="hover:bg-primary/5 transition-colors">
                                                    {Object.values(row).map((val: any, j) => (
                                                        <TableCell key={j}>
                                                            {typeof val === 'number' ? val.toFixed(2) : val}
                                                        </TableCell>
                                                    ))}
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-20 bg-muted/20 rounded-lg border-2 border-dashed">
                                    <Filter className="w-12 h-12 text-muted-foreground/30 mb-4" />
                                    <p className="text-muted-foreground">Run a scan to see technical findings here.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
