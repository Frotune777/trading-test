'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface ReadinessStripProps {
  quality: {
    total_pillars: number;
    active_pillars: number;
    placeholder_pillars: number;
    failed_pillars: string[];
  };
  sampleCount: number;
}

const Metric = ({ label, value, status }: { label: string; value: string; status: 'success' | 'warning' | 'error' }) => (
  <div className="flex flex-col">
    <span className="text-[9px] uppercase font-bold text-muted-foreground leading-none mb-1">{label}</span>
    <div className={cn(
      "text-xs font-black leading-none",
      status === 'success' ? 'text-emerald-500' : status === 'warning' ? 'text-amber-500' : 'text-rose-500'
    )}>
      {value}
    </div>
  </div>
);

export default function ReadinessStrip({ quality, sampleCount }: ReadinessStripProps) {
  const isDegraded = quality.failed_pillars.length > 0 || quality.placeholder_pillars > 0;

  return (
    <div className="w-full bg-background/50 border border-border rounded-xl overflow-hidden backdrop-blur-sm shadow-sm">
      <div className="grid grid-cols-12 h-full">
        <div className="col-span-12 lg:col-span-3 flex items-center px-4 py-3 bg-muted/30 border-r border-border">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isDegraded ? "bg-amber-500" : "bg-emerald-500 animate-pulse"
            )} />
            <span className="text-[10px] font-black uppercase tracking-tighter text-foreground whitespace-nowrap">
              Reasoning Health
            </span>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-9 flex items-center justify-between px-6 py-3" data-testid="readiness-metrics">
          <Metric
            label="Historical Depth"
            value={`${sampleCount} Samples`}
            status={sampleCount >= 30 ? 'success' : 'warning'}
          />
          <Metric
            label="Confidence Matrix"
            value={`${quality.active_pillars}/${quality.total_pillars} Active`}
            status={quality.active_pillars >= 5 ? 'success' : 'warning'}
          />
          <Metric
            label="System State"
            value={isDegraded ? "DEGRADED" : "OPTIMAL"}
            status={isDegraded ? 'warning' : 'success'}
          />

          <div className="flex items-center gap-3">
            <div className="text-[9px] uppercase font-bold text-muted-foreground leading-none">Confidence</div>
            <div className="flex gap-1" data-testid="confidence-dots">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className={cn(
                    "w-1.5 h-3 rounded-sm transition-all duration-700",
                    i <= quality.active_pillars ? "bg-primary animate-pulse" : "bg-muted"
                  )}
                  style={{ animationDelay: `${i * 100}ms` }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
