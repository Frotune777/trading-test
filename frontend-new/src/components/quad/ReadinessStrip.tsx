'use client';

import React from 'react';
import { 
  Database, 
  BarChart, 
  Share2, 
  ShieldAlert, 
  CheckCircle2, 
  Info, 
  Layers, 
  Activity
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ReadinessItemProps {
  label: string;
  status: 'READY' | 'COLLECTING' | 'INSUFFICIENT' | 'FAILED';
  meta?: string;
  icon: React.ReactNode;
}

function ReadinessItem({ label, status, meta, icon }: ReadinessItemProps) {
  const getStatusColor = (s: string) => {
    switch (s) {
      case 'READY': return 'text-emerald-500';
      case 'COLLECTING': return 'text-amber-500';
      case 'INSUFFICIENT': return 'text-slate-500';
      case 'FAILED': return 'text-rose-500';
      default: return 'text-slate-500';
    }
  };

  const getStatusBg = (s: string) => {
    switch (s) {
      case 'READY': return 'bg-emerald-500/10';
      case 'COLLECTING': return 'bg-amber-500/10';
      case 'INSUFFICIENT': return 'bg-slate-500/10';
      case 'FAILED': return 'bg-rose-500/10';
      default: return 'bg-slate-500/10';
    }
  };

  return (
    <div className="flex items-center gap-3 px-4 py-2 border-r border-slate-800 last:border-r-0 group cursor-default">
      <div className={cn("p-1.5 rounded-md", getStatusBg(status))}>
        {React.isValidElement(icon) ? React.cloneElement(icon as React.ReactElement<any>, { className: cn("w-4 h-4", getStatusColor(status)) }) : icon}
      </div>
      <div>
        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-tight leading-none mb-1">{label}</div>
        <div className="flex items-center gap-2">
          <span className={cn("text-xs font-mono font-bold leading-none", getStatusColor(status))}>
            {status}
          </span>
          {meta && (
            <span className="text-[10px] text-slate-600 font-mono leading-none">
              [{meta}]
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

interface ReadinessStripProps {
  quality: {
    active_pillars: number;
    total_pillars: number;
    placeholder_pillars: number;
    failed_pillars: string[];
  };
  sampleCount?: number;
}

export default function ReadinessStrip({ quality, sampleCount = 0 }: ReadinessStripProps) {
  // Logic to determine readiness states based on quality metrics
  const historyStatus = sampleCount >= 10 ? 'READY' : sampleCount > 0 ? 'COLLECTING' : 'INSUFFICIENT';
  const accuracyStatus = quality.active_pillars >= 5 ? 'READY' : quality.active_pillars >= 3 ? 'COLLECTING' : 'INSUFFICIENT';
  const correlationStatus = sampleCount >= 30 ? 'READY' : 'INSUFFICIENT';
  const stabilityStatus = quality.failed_pillars.length === 0 ? 'READY' : 'FAILED';

  return (
    <div className="w-full bg-slate-950 border border-slate-800 rounded-lg flex flex-wrap items-center overflow-hidden shadow-sm">
      <ReadinessItem 
        label="Historical Depth" 
        status={historyStatus} 
        meta={sampleCount > 0 ? `${sampleCount} SAMPLES` : 'MIN 10 REQ'}
        icon={<Database />}
      />
      <ReadinessItem 
        label="Model Accuracy" 
        status={accuracyStatus} 
        meta={`${quality.active_pillars}/${quality.total_pillars} ACTIVE`}
        icon={<CheckCircle2 />}
      />
      <ReadinessItem 
        label="Structural Stability" 
        status={stabilityStatus} 
        meta={quality.failed_pillars.length > 0 ? 'ERRORS DETECTED' : 'NOMINAL'}
        icon={<Activity />}
      />
      <ReadinessItem 
        label="Correlation Validity" 
        status={correlationStatus} 
        meta={sampleCount < 30 ? 'LOW COVARIANCE' : 'VALIDATED'}
        icon={<Share2 />}
      />
      
      {/* Readiness Summary Badge */}
      <div className="ml-auto flex items-center gap-3 px-6 h-full bg-slate-900 border-l border-slate-800 py-3">
        <div className="text-right">
          <div className="text-[9px] uppercase font-bold text-slate-500 leading-none mb-1">System State</div>
          <div className={cn(
             "text-xs font-black leading-none",
             quality.placeholder_pillars > 0 ? "text-amber-500" : "text-emerald-500"
          )}>
            {quality.placeholder_pillars > 0 ? 'DEGRADED' : 'OPTIMAL'}
          </div>
        </div>
      </div>
    </div>
  );
}

