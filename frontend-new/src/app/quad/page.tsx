'use client';

import React, { useEffect, useState } from 'react';

import { useQuadAnalytics } from '@/hooks/useQuadAnalytics';
import { useMarket } from "@/context/market-context"
import CommandCard from '@/components/quad/CommandCard';
import ReadinessStrip from '@/components/quad/ReadinessStrip';
import PillarContribution from '@/components/quad/PillarContribution';
import ConvictionTimeline from '@/components/quad/conviction-timeline';
import PerformanceTracker from '@/components/quad/PerformanceTracker';
import CorrelationMatrix from '@/components/quad/CorrelationMatrix';
import AlertManager from '@/components/quad/AlertManager';
import RiskMetrics from '@/components/quad/RiskMetrics';
import TradeSetup from '@/components/quad/TradeSetup';
import PriceChart from '@/components/charts/PriceChart';
import VolumeProfile from '@/components/charts/VolumeProfile';
import SignalAccuracy from '@/components/quad/SignalAccuracy';
import PeerComparison from '@/components/quad/PeerComparison';
import BacktestResults from '@/components/quad/BacktestResults';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  History, 
  BarChart4, 
  Layers, 
  ShieldCheck, 
  Info,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import PillarDrift from '@/components/quad/pillar-drift';
import DecisionHistory from '@/components/quad/decision-history';

function ClientTime() {
  const [time, setTime] = useState<string>('');
  
  useEffect(() => {
    setTime(new Date().toLocaleTimeString());
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return <span>SYS-TIME: {time || '--:--:--'}</span>;
}

export default function QUADDashboard() {
  const { symbol } = useMarket()
  const { reasoning, statistics, timeline, loading, error, fetchAll } = useQuadAnalytics();

  useEffect(() => {
    fetchAll(symbol);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]); // Re-fetch when global symbol changes

  return (
      <div className="p-0 space-y-4 animate-in fade-in duration-700">
        {/* Institutional Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-1 border-b border-border">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                <Layers className="w-5 h-5 text-primary-foreground" />
              </div>
              <h1 className="text-2xl font-black tracking-tighter uppercase italic">QUAD Analytics</h1>
              <Badge variant="outline" className="border-primary/30 text-primary bg-primary/5 px-2 text-[10px]">v1.1.0-STABLE</Badge>
            </div>
            <p className="text-muted-foreground text-[10px] font-medium uppercase tracking-wider">Institutional Multi-Dimensional Reasoning & Risk Calibration</p>
          </div>
          
          {/* Symbol selector is now in global Header */}
        </div>
        
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
            <div className="text-muted-foreground font-mono text-xs tracking-widest animate-pulse">CALIBRATING {symbol} MATRIX...</div>
          </div>
        ) : error ? (
          <div className="p-8 bg-destructive/5 border border-destructive/20 rounded-xl text-center space-y-4">
            <ShieldCheck className="w-10 h-10 text-destructive mx-auto" />
            <h2 className="text-lg font-bold text-foreground">Analysis Sync Failed</h2>
            <p className="text-muted-foreground text-xs max-w-md mx-auto">{error}</p>
            <button 
              onClick={() => fetchAll(symbol)}
              className="px-4 py-1.5 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-lg transition-colors font-bold text-xs border border-border"
            >
              RETRY CONNECTION
            </button>
          </div>
        ) : reasoning ? (
          <div className="space-y-4 max-w-[1600px] mx-auto animate-in fade-in duration-700">
            {/* Command Section */}
            <section className="space-y-4">
              <CommandCard 
                symbol={reasoning!.symbol}
                signal={reasoning!.directional_bias as any}
                conviction={reasoning!.conviction_score}
                confidence={reasoning!.quality.active_pillars >= 5 ? 'HIGH' : reasoning!.quality.active_pillars >= 3 ? 'MEDIUM' : 'LOW'}
                regime={reasoning!.market_context?.regime || 'NEUTRAL'}
                timestamp={reasoning!.analysis_timestamp}
                dataWindow="30D SLIDING WINDOW"
                isExecutionReady={reasoning!.is_execution_ready}
              />
              <ReadinessStrip 
                quality={reasoning!.quality} 
                sampleCount={statistics?.total_decisions || 0}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <RiskMetrics symbol={symbol} />
                <TradeSetup symbol={symbol} />
              </div>
            </section>

            {/* Pillar Contributions & Narrative */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
              <div className="xl:col-span-8 space-y-4 min-w-0">
                <PriceChart symbol={symbol} />
                <PillarContribution pillars={reasoning.pillar_scores} />
                
                <Card className="bg-card border-border overflow-hidden">
                  <CardHeader className="py-2 px-4 border-b border-border bg-muted/30">
                    <CardTitle className="text-[10px] uppercase tracking-widest text-muted-foreground font-black">Reasoning Narrative Output</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <p className="text-foreground leading-relaxed text-sm font-medium">
                      {reasoning!.reasoning}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="xl:col-span-4 space-y-4 min-w-0">
                <ConvictionTimeline symbol={symbol} days={30} />
                <PillarDrift symbol={symbol} />
                <VolumeProfile symbol={symbol} />
              </div>
            </div>



            <div className="space-y-2">
               <div className="flex items-center justify-between px-1">
                  <h3 className="text-[10px] uppercase tracking-[0.2em] font-black text-muted-foreground">Decision History Log</h3>
                  <Badge variant="outline" className="text-[9px] border-border text-muted-foreground bg-muted/20">ARCHIVE</Badge>
               </div>
               <DecisionHistory symbol={symbol} limit={20} />
            </div>

            {/* Advanced Metrics & Performance Analysis */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
              {/* Correlation & Context */}
              <div className="xl:col-span-4 space-y-4 min-w-0">
                <div className="space-y-2">
                  <div className="flex items-center justify-between px-1">
                    <h3 className="text-[10px] uppercase tracking-[0.2em] font-black text-muted-foreground">Cross-Pillar Correlation</h3>
                    {(!statistics || statistics.total_decisions < 30) && (
                      <Badge variant="outline" className="text-[9px] border-border text-muted-foreground bg-muted/20">INSUFFICIENT DATA</Badge>
                    )}
                  </div>
                  {statistics && statistics.total_decisions >= 30 ? (
                    <CorrelationMatrix symbol={symbol} days={90} />
                  ) : (
                    <div className="bg-muted/10 border border-border rounded-xl p-8 text-center flex flex-col items-center justify-center space-y-3 h-[300px]">
                      <div className="p-3 bg-muted/20 rounded-full border border-border">
                        <BarChart4 className="w-6 h-6 text-muted-foreground" />
                      </div>
                      <div>
                        <h4 className="text-muted-foreground font-bold mb-1 uppercase tracking-wider text-[11px]">Correlation Baseline Pending</h4>
                        <p className="text-muted-foreground/60 text-[10px] max-w-xs mx-auto italic">
                          Statistical covariance mapping requires a minimum of 30 historical decisions. 
                        </p>
                      </div>
                    </div>
                  )}
                </div>
                <PeerComparison symbol={symbol} />
              </div>

              {/* Performance Analysis */}
              <div className="xl:col-span-8 space-y-4 min-w-0">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <SignalAccuracy symbol={symbol} />
                  <BacktestResults symbol={symbol} />
                </div>
                
                <div className="space-y-2">
                  <h3 className="text-[10px] uppercase tracking-[0.2em] font-black text-muted-foreground">Signal Persistence & Alerts</h3>
                  <AlertManager symbol={symbol} />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-40 text-center space-y-6">
            <History className="w-16 h-16 text-muted" />
            <div className="space-y-2">
              <h2 className="text-2xl font-black tracking-tight text-foreground">NO SYMBOL SELECTED</h2>
              <p className="text-muted-foreground text-sm max-w-xs mx-auto">Please select a validated instrument from the terminal to begin multi-dimensional analysis.</p>
            </div>
          </div>
        )}

        {/* Institutional Footer Sync */}
        <div className="mt-12 pt-8 border-t border-border flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] text-muted-foreground font-bold tracking-widest uppercase">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-primary" /> TRADING-TEST-NET</span>
            <span className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-primary" /> FEED-HEALTH: <span className="text-emerald-500">NOMINAL</span></span>
          </div>
          <div className="flex items-center gap-4">
             <ClientTime />
             <span className="text-foreground px-2 py-0.5 bg-muted rounded">ENCRYPTION: AES-256-GCM</span>
          </div>
        </div>
      </div>
  );
}
