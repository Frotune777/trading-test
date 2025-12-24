"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import MarketOverview from '../components/market/market-overview';
import CandlestickChart from '../components/charts/candlestick-chart';
import PredictionCard from '../components/stock/prediction-card';
import ConvictionTimeline from '../components/quad/conviction-timeline';
import PillarDrift from '../components/quad/pillar-drift';
import DecisionHistory from '../components/quad/decision-history';

export default function DashboardPage() {
    const [selectedSymbol, setSelectedSymbol] = React.useState('RELIANCE');

    return (
        <div className="flex flex-col gap-6 p-6 bg-slate-950 min-h-screen text-slate-50">
            <header className="flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight">Fortune Trading QUAD</h1>
                <div className="flex gap-4">
                    {/* Symbol Selector Component */}
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Main Chart Area */}
                <div className="lg:col-span-3">
                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle>{selectedSymbol} (NSE)</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[500px]">
                            <CandlestickChart symbol={selectedSymbol} timeframe="1D" />
                        </CardContent>
                    </Card>
                </div>

                {/* Prediction & Sidebar Area */}
                <div className="flex flex-col gap-6">
                    <PredictionCard symbol={selectedSymbol} />
                    <Card className="bg-slate-900 border-slate-800">
                        <CardHeader>
                            <CardTitle>Technical Signals</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <span>RSI (14)</span>
                                    <span className="text-orange-400">42.5 (Neutral)</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Trend</span>
                                    <span className="text-green-400">Bullish</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            <Tabs defaultValue="overview" className="w-full">
                <TabsList className="bg-slate-900 border-slate-800">
                    <TabsTrigger value="overview">Market Overview</TabsTrigger>
                    <TabsTrigger value="quad-analytics">QUAD Analytics</TabsTrigger>
                    <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
                    <TabsTrigger value="screener">Screener</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview">
                    <MarketOverview />
                </TabsContent>
                
                <TabsContent value="quad-analytics" className="space-y-6">
                    {/* QUAD v1.1 Analytics */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <ConvictionTimeline symbol={selectedSymbol} days={30} />
                        <PillarDrift symbol={selectedSymbol} />
                    </div>
                    <DecisionHistory symbol={selectedSymbol} limit={10} />
                </TabsContent>
                
                <TabsContent value="fundamentals">
                    {/* Fundamentals content */}
                    <Card className="bg-slate-900 border-slate-800">
                        <CardContent className="p-6">
                            <p className="text-slate-400">Fundamentals data coming soon...</p>
                        </CardContent>
                    </Card>
                </TabsContent>
                
                <TabsContent value="screener">
                    {/* Screener content */}
                    <Card className="bg-slate-900 border-slate-800">
                        <CardContent className="p-6">
                            <p className="text-slate-400">Screener coming soon...</p>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
