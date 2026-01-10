
"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDataIngestion } from "@/hooks/useDataIngestion";
import { DataAvailabilityCard } from "@/components/data/DataAvailabilityCard";
import { AlertCircle, CheckCircle2, Download, RefreshCw, Search, History } from "lucide-react";

export default function MarketDataIngestion() {
  const { 
    availability, 
    ingestionResult, 
    loading, 
    checkAvailability, 
    ingestData 
  } = useDataIngestion();

  // Local state for form inputs
  const [symbol, setSymbol] = useState("");
  const [source, setSource] = useState("yahoo");
  const [timeframe, setTimeframe] = useState("1d");
  
  // Default to empty to prevent hydration mismatch
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Initialize dates on client-side only
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const lastYear = new Date(new Date().setFullYear(new Date().getFullYear() - 1)).toISOString().split('T')[0];
    setStartDate(lastYear);
    setEndDate(today);
  }, []);

  // Check availability on mount or symbol change
  // Removed automatic check on symbol change to prevent rapid API calls
  // User must click "Refresh Status" manually

  const handleIngest = () => {
    if (!symbol || !startDate || !endDate) return;
    ingestData(symbol, startDate, endDate, source, timeframe);
  };

  return (
    <div className="container mx-auto p-6 space-y-6 bg-slate-950 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Market Data Manager</h1>
          <p className="text-slate-400">Manual data ingestion and validation for QUAD Analysis</p>
        </div>
        <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => checkAvailability(symbol)} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh Status
            </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Controls */}
        <Card className="md:col-span-2 border-slate-800 bg-slate-950">
          <CardHeader>
            <CardTitle className="text-lg text-slate-200">Ingestion Controls</CardTitle>
            <CardDescription>Configure data fetch parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase">Symbol</label>
                <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                    <Input 
                        value={symbol} 
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        className="pl-9 bg-slate-900 border-slate-700 text-slate-100 font-mono"
                        placeholder="e.g. RELIANCE"
                    />
                </div>
              </div>

               <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase">Data Source</label>
                <Select value={source} onValueChange={setSource}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-100">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800">
                    <SelectItem value="yahoo">Yahoo Finance (Free)</SelectItem>
                    <SelectItem value="openalgo" disabled>OpenAlgo (Premium)</SelectItem>
                    <SelectItem value="nse" disabled>NSE Direct (Enterprises)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
               <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase">Timeframe</label>
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-slate-100">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800">
                    <SelectItem value="1d">Daily (1D)</SelectItem>
                    <SelectItem value="1h" disabled>Hourly (1H)</SelectItem>
                    <SelectItem value="15m" disabled>15 Minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>

               <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase">Start Date</label>
                <Input 
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="bg-slate-900 border-slate-700 text-slate-100"
                />
              </div>

               <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase">End Date</label>
                <Input 
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="bg-slate-900 border-slate-700 text-slate-100"
                />
              </div>
            </div>

            <div className="pt-4 flex justify-end">
                <Button 
                    onClick={handleIngest} 
                    disabled={loading || !symbol}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white min-w-[150px]"
                >
                    {loading ? (
                        <>
                            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            Ingesting...
                        </>
                    ) : (
                        <>
                            <Download className="mr-2 h-4 w-4" />
                            Fetch & Store
                        </>
                    )}
                </Button>
            </div>

            {ingestionResult && (
                <div className={`mt-4 p-4 rounded-md border ${
                    ingestionResult.status === 'success' 
                        ? 'bg-emerald-950/30 border-emerald-900 text-emerald-400' 
                        : 'bg-rose-950/30 border-rose-900 text-rose-400'
                }`}>
                    <div className="flex items-center gap-2 mb-2 font-semibold">
                        {ingestionResult.status === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                        Ingestion {ingestionResult.status === 'success' ? 'Complete' : 'Failed'}
                    </div>
                    {ingestionResult.status === 'success' ? (
                        <div className="text-sm space-y-1 text-slate-400">
                            <p>Rows Fetched: <span className="text-slate-200 font-mono">{ingestionResult.rows_fetched}</span></p>
                            <p>Rows Stored: <span className="text-slate-200 font-mono">{ingestionResult.rows_inserted}</span></p>
                            <p>Range: <span className="text-slate-200 font-mono">{ingestionResult.date_range?.[0]}</span> to <span className="text-slate-200 font-mono">{ingestionResult.date_range?.[1]}</span></p>
                        </div>
                    ) : (
                        <p className="text-sm">{ingestionResult.message}</p>
                    )}
                </div>
            )}

          </CardContent>
        </Card>

        {/* Right Column: Status */}
        <div className="space-y-6">
            <DataAvailabilityCard 
                data={availability} 
                loading={loading && !ingestionResult} // Only show loading spinner if checkAvailability is running, not ingestion
                selectedRange={{ start: startDate, end: endDate }}
            />
            
            <Card className="border-slate-800 bg-slate-950/50">
               <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
                        <History className="h-4 w-4" />
                        INGESTION RULES
                    </CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-slate-500 space-y-2">
                    <p>• Data is fetched from selected source and normalized.</p>
                    <p>• Existing records are safely updated (Idempotent).</p>
                    <p>• QUAD Analysis only runs on stored data.</p>
                    <p>• Ensure "Coverage Complete" before running analysis.</p>
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  );
}
