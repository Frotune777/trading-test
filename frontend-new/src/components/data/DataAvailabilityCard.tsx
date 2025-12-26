
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CheckCircle, Database } from 'lucide-react';

interface DataAvailability {
  symbol: string;
  has_data: boolean;
  start_date: string | null;
  end_date: string | null;
  count: number;
}

interface DataAvailabilityCardProps {
  data: DataAvailability | null;
  loading: boolean;
  selectedRange?: { start: string; end: string };
}

export const DataAvailabilityCard: React.FC<DataAvailabilityCardProps> = ({ 
  data, 
  loading,
  selectedRange 
}) => {
  if (loading) {
    return (
      <Card className="border-slate-800 bg-slate-950/50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-slate-400">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-500" />
            <span className="text-sm font-mono">Checking availability...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="border-slate-800 bg-slate-950/50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-slate-500">
            <Database className="h-4 w-4" />
            <span className="text-sm">Select a symbol to check data availability</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const hasGap = selectedRange && data.has_data && 
    (new Date(selectedRange.start) < new Date(data.start_date!) || 
     new Date(selectedRange.end) > new Date(data.end_date!));

  return (
    <Card className="border-slate-800 bg-slate-950 shadow-lg">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-400">
          <Database className="h-4 w-4 text-emerald-500" />
          DATABASE STATUS
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!data.has_data ? (
          <div className="rounded-md border border-amber-900/30 bg-amber-950/20 p-4">
            <div className="flex items-center gap-2 text-amber-500">
              <AlertCircle className="h-5 w-5" />
              <span className="font-semibold">No Data stored for {data.symbol}</span>
            </div>
            <p className="mt-1 text-xs text-amber-400/70">
              QUAD analysis cannot run until data is ingested.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">Range</div>
                <div className="font-mono text-sm text-slate-200">
                  {data.start_date} <span className="text-slate-600">→</span> {data.end_date}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500 uppercase tracking-wider">Total Rows</div>
                <div className="font-mono text-lg font-bold text-emerald-400">
                  {data.count.toLocaleString()}
                </div>
              </div>
            </div>

            {hasGap && (
              <div className="rounded border border-blue-900/30 bg-blue-900/10 p-3 text-xs">
                <div className="flex items-center gap-2 text-blue-400 mb-1">
                  <AlertCircle className="h-3 w-3" />
                  <span className="font-medium">Ingestion Required</span>
                </div>
                <div className="text-slate-400">
                  Requested range extends beyond stored data. Ingestion will fill gaps.
                </div>
              </div>
            )}
            
            {!hasGap && selectedRange && (
               <div className="rounded border border-emerald-900/30 bg-emerald-900/10 p-3 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 mb-1">
                  <CheckCircle className="h-3 w-3" />
                  <span className="font-medium">Coverage Complete</span>
                </div>
                <div className="text-slate-400">
                  Database already covers the requested date range.
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
