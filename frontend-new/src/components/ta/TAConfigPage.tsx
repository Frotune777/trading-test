'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { taConfigAPI } from '@/lib/api/ta-api';
import { Loader2, Settings2, BarChart3, Target, ShieldAlert, CheckCircle2, ChevronRight } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import RegimeWeightsEditor from './RegimeWeightsEditor';
import TAAccuracyChart from './TAAccuracyChart';

const TAConfigPage: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [weights, setWeights] = useState<Record<string, Record<string, number>>>({});
    const [accuracy, setAccuracy] = useState<any>(null);
    const [performance, setPerformance] = useState<any[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [weightsData, accuracyData, performanceData] = await Promise.all([
                taConfigAPI.getAllWeights(),
                taConfigAPI.getAccuracyMetrics(),
                taConfigAPI.getIndicatorPerformance()
            ]);
            setWeights(weightsData);
            setAccuracy(accuracyData);
            setPerformance(performanceData);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateWeights = async (regime: string, newWeights: Record<string, number>) => {
        try {
            await taConfigAPI.updateRegimeWeights(regime, newWeights);
            setWeights(prev => ({
                ...prev,
                [regime]: newWeights
            }));
        } catch (err: any) {
            alert(`Failed to update weights: ${err.message}`);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[400px]">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-1">
                <h2 className="text-3xl font-bold tracking-tight">TA Aggregator</h2>
                <p className="text-muted-foreground">Manage adaptive indicator weighting and track accuracy performance.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatsCard
                    title="Overall Accuracy"
                    value={`${(accuracy?.overall_accuracy * 100).toFixed(1)}%`}
                    description="Last 30 days"
                    icon={<Target className="w-4 h-4 text-blue-500" />}
                />
                <StatsCard
                    title="Optimal Regime"
                    value={accuracy?.best_regime?.replace('_', ' ')}
                    description="Highest predictive power"
                    icon={<CheckCircle2 className="w-4 h-4 text-green-500" />}
                />
                <StatsCard
                    title="Caution Regime"
                    value={accuracy?.worst_regime?.replace('_', ' ')}
                    description="Low confidence signals"
                    icon={<ShieldAlert className="w-4 h-4 text-red-500" />}
                />
            </div>

            <Tabs defaultValue="weights" className="space-y-4">
                <TabsList className="bg-slate-900 border-slate-800">
                    <TabsTrigger value="weights" className="gap-2">
                        <Settings2 className="w-4 h-4" />
                        Regime Weights
                    </TabsTrigger>
                    <TabsTrigger value="accuracy" className="gap-2">
                        <BarChart3 className="w-4 h-4" />
                        Accuracy Analysis
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="weights" className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {Object.keys(weights).map((regime) => (
                            <RegimeWeightsEditor
                                key={regime}
                                regime={regime}
                                weights={weights[regime]}
                                onSave={(newWeights: Record<string, number>) => handleUpdateWeights(regime, newWeights)}
                            />
                        ))}
                    </div>
                </TabsContent>

                <TabsContent value="accuracy" className="space-y-4">
                    <TAAccuracyChart accuracy={accuracy} performance={performance} />
                </TabsContent>
            </Tabs>
        </div>
    );
};

const StatsCard = ({ title, value, description, icon }: any) => (
    <Card className="bg-slate-950 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{title}</CardTitle>
            {icon}
        </CardHeader>
        <CardContent>
            <div className="text-2xl font-bold">{value}</div>
            <p className="text-xs text-muted-foreground">{description}</p>
        </CardContent>
    </Card>
);

export default TAConfigPage;
