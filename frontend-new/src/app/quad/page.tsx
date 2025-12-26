'use client';

import React, { useState, useEffect } from 'react';
import MainLayout from "@/components/layout/main-layout";
import { useQuadAnalytics } from '@/hooks/useQuadAnalytics';
import CommandCard from '@/components/quad/CommandCard';
import ReadinessStrip from '@/components/quad/ReadinessStrip';
import PillarContribution from '@/components/quad/PillarContribution';
import ConvictionTimeline from '@/components/quad/conviction-timeline';
import PerformanceTracker from '@/components/quad/PerformanceTracker';
import CorrelationMatrix from '@/components/quad/CorrelationMatrix';
import AlertManager from '@/components/quad/AlertManager';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  History, 
  BarChart4, 
  Layers, 
  ShieldCheck, 
  Info,
  ChevronRight,
  Database
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function QUADDashboard() {
  const [symbol, setSymbol] = useState('RELIANCE');
  const { reasoning, statistics, timeline, loading, error, fetchAll } = useQuadAnalytics();

  useEffect(() => {
    fetchAll(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSymbolChange = (newSymbol: string) => {
    setSymbol(newSymbol);
    fetchAll(newSymbol);
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 space-y-8">
        {/* Institutional Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Layers className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-3xl font-black tracking-tighter uppercase italic">QUAD Analytics</h1>
              <Badge variant="outline" className="border-blue-500/30 text-blue-400 bg-blue-500/5 px-2">v1.1.0-STABLE</Badge>
            </div>
            <p className="text-slate-500 text-sm font-medium">Institutional Multi-Dimensional Reasoning & Risk Calibration Engine</p>
          </div>

          <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-xl border border-slate-800">
            <div className="flex items-center gap-2 pl-2">
              <Database className="w-4 h-4 text-slate-500" />
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Select Instrument:</span>
            </div>
            <select
              value={symbol}
              onChange={(e) => handleSymbolChange(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm font-black text-white focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer min-w-[140px]"
            >
              <option value="RELIANCE">RELIANCE</option>
              <option value="TCS">TCS</option>
              <option value="INFY">INFY</option>
              <option value="HDFCBANK">HDFCBANK</option>
              <option value="ICICIBANK">ICICIBANK</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
            <div className="text-slate-500 font-mono tracking-widest animate-pulse">CALIBRATING {symbol} MATRIX...</div>
          </div>
        ) : error ? (
          <div className="p-12 bg-rose-500/5 border border-rose-500/20 rounded-2xl text-center space-y-4">
            <ShieldCheck className="w-12 h-12 text-rose-500 mx-auto" />
            <h2 className="text-xl font-bold text-white">Analysis Sync Failed</h2>
            <p className="text-slate-400 max-w-md mx-auto">{error}</p>
            <button 
              onClick={() => fetchAll(symbol)}
              className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors font-bold text-sm"
            >
              RETRY CONNECTION
            </button>
          </div>
        ) : reasoning ? (
          <div className="space-y-8 max-w-[1600px] mx-auto animate-in fade-in duration-700">
            {/* Command Section */}
            <section className="space-y-6">
              <CommandCard 
                symbol={reasoning.symbol}
                signal={reasoning.directional_bias as any}
                conviction={reasoning.conviction_score}
                confidence={reasoning.quality.active_pillars >= 5 ? 'HIGH' : reasoning.quality.active_pillars >= 3 ? 'MEDIUM' : 'LOW'}
                regime={reasoning.market_context?.regime || 'NEUTRAL'}
                timestamp={reasoning.analysis_timestamp}
                dataWindow="30D SLIDING WINDOW"
                isExecutionReady={reasoning.is_execution_ready}
              />
              <ReadinessStrip 
                quality={reasoning.quality} 
                sampleCount={statistics?.total_decisions || 0}
              />
            </section>

            {/* Pillar Contributions & Narrative */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
              <div className="xl:col-span-8 space-y-8">
                <PillarContribution pillars={reasoning.pillar_scores} />
                
                <Card className="bg-slate-900 border-slate-800 overflow-hidden">
                  <CardHeader className="py-4 border-b border-slate-800 bg-slate-900/50">
                    <CardTitle className="text-xs uppercase tracking-widest text-slate-500 font-black">Reasoning Narrative Output</CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <p className="text-slate-300 leading-relaxed font-medium">
                      {reasoning.reasoning}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="xl:col-span-4 space-y-8">
                <ConvictionTimeline symbol={symbol} days={30} />
                <PerformanceTracker symbol={symbol} days={90} />
              </div>
            </div>

            <Separator className="bg-slate-800" />

            {/* Advanced Metrics */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <h3 className="text-xs uppercase tracking-[0.2em] font-black text-slate-500">Cross-Pillar Correlation</h3>
                  {(!statistics || statistics.total_decisions < 30) && (
                    <Badge variant="outline" className="text-[10px] border-slate-800 text-slate-600 bg-slate-950">INSUFFICIENT DATA</Badge>
                  )}
                </div>
                {statistics && statistics.total_decisions >= 30 ? (
                  <CorrelationMatrix symbol={symbol} days={90} />
                ) : (
                  <div className="bg-slate-900/30 border border-slate-800/50 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4 h-[400px]">
                    <div className="p-4 bg-slate-950 rounded-full border border-slate-800">
                      <BarChart4 className="w-8 h-8 text-slate-700" />
                    </div>
                    <div>
                      <h4 className="text-slate-400 font-bold mb-1 uppercase tracking-wider text-sm">Correlation Baseline Pending</h4>
                      <p className="text-slate-600 text-[11px] max-w-xs mx-auto italic">
                        Statistical covariance mapping requires a minimum of 30 historical decisions. 
                        Currently tracking at <span className="text-blue-500 font-bold">{statistics?.total_decisions || 0}/30</span> nodes.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <h3 className="text-xs uppercase tracking-[0.2em] font-black text-slate-500">Signal Persistence & Alerts</h3>
                <AlertManager symbol={symbol} />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-40 text-center space-y-6">
            <History className="w-16 h-16 text-slate-800" />
            <div className="space-y-2">
              <h2 className="text-2xl font-black tracking-tight">NO SYMBOL SELECTED</h2>
              <p className="text-slate-500 text-sm max-w-xs mx-auto">Please select a validated instrument from the terminal to begin multi-dimensional analysis.</p>
            </div>
          </div>
        )}

        {/* Institutional Footer Sync */}
        <div className="mt-12 pt-8 border-t border-slate-900 flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] text-slate-600 font-bold tracking-widest uppercase">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-blue-500" /> TRADING-TEST-NET</span>
            <span className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-blue-500" /> FEED-HEALTH: <span className="text-emerald-500">NOMINAL</span></span>
          </div>
          <div className="flex items-center gap-4">
             <span>SYS-TIME: {new Date().toLocaleTimeString()}</span>
             <span className="text-slate-800 px-2 py-0.5 bg-slate-900 rounded">ENCRYPTION: AES-256-GCM</span>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
