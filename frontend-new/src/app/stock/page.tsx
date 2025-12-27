'use client';

import { Search, TrendingUp, Star, Activity, ArrowUpRight, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Popular NSE stocks
const POPULAR_STOCKS = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', sector: 'Energy' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'IT' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', sector: 'Banking' },
  { symbol: 'INFY', name: 'Infosys', sector: 'IT' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank', sector: 'Banking' },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever', sector: 'FMCG' },
  { symbol: 'ITC', name: 'ITC Limited', sector: 'FMCG' },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel', sector: 'Telecom' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', sector: 'Banking' },
  { symbol: 'LT', name: 'Larsen & Toubro', sector: 'Infrastructure' },
  { symbol: 'AXISBANK', name: 'Axis Bank', sector: 'Banking' },
  { symbol: 'ASIANPAINT', name: 'Asian Paints', sector: 'Paints' },
  { symbol: 'MARUTI', name: 'Maruti Suzuki', sector: 'Auto' },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical', sector: 'Pharma' },
  { symbol: 'TITAN', name: 'Titan Company', sector: 'Consumer Goods' },
  { symbol: 'WIPRO', name: 'Wipro', sector: 'IT' },
  { symbol: 'ULTRACEMCO', name: 'UltraTech Cement', sector: 'Cement' },
  { symbol: 'NESTLEIND', name: 'Nestle India', sector: 'FMCG' },
  { symbol: 'TATAMOTORS', name: 'Tata Motors', sector: 'Auto' },
];

export default function StockListPage() {

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Stock Analysis</h1>
          <p className="text-muted-foreground">
            Analyze market leaders with our 6-pillar QUAD reasoning engine
          </p>
        </div>
      </div>

      {/* Quick Actions at Top */}
      <div className="grid gap-4 md:grid-cols-2">
           <Link href="/quad">
            <Card className="hover:bg-accent/50 transition-colors cursor-pointer border-primary/20 bg-card">
                <CardContent className="p-4 flex items-center gap-4">
                    <div className="p-2 bg-primary/10 rounded-lg">
                        <TrendingUp className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-bold text-foreground">Institutional QUAD Analytics</h3>
                        <p className="text-xs text-muted-foreground">Deep-dive multi-dimensional reasoning</p>
                    </div>
                    <ArrowUpRight className="ml-auto h-4 w-4 text-muted-foreground" />
                </CardContent>
            </Card>
           </Link>
           <Link href="/dashboard/screener">
            <Card className="hover:bg-accent/50 transition-colors cursor-pointer border-success/20 bg-card">
                <CardContent className="p-4 flex items-center gap-4">
                    <div className="p-2 bg-success/10 rounded-lg">
                        <Activity className="h-6 w-6 text-success" />
                    </div>
                    <div>
                        <h3 className="font-bold text-foreground">Market Screener</h3>
                        <p className="text-xs text-muted-foreground">Scan for opportunities across sectors</p>
                    </div>
                     <ArrowUpRight className="ml-auto h-4 w-4 text-muted-foreground" />
                </CardContent>
            </Card>
           </Link>
      </div>

      {/* Popular Stocks Grid */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Star className="h-5 w-5 text-yellow-500" />
          <h2 className="text-xl font-semibold">Market Leaders</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {POPULAR_STOCKS.map((stock) => (
            <Link key={stock.symbol} href={`/stock/${stock.symbol}`}>
              <Card className="hover:shadow-lg transition-all hover:border-primary/50 cursor-pointer bg-card border-border">
                <CardHeader className="pb-3 pt-4 px-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-bold tracking-tight">{stock.symbol}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
                        {stock.name}
                      </p>
                    </div>
                    <Badge variant="outline" className="text-[10px] uppercase font-mono bg-muted border-border text-muted-foreground">
                        {stock.sector}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pb-4 px-4">
                  <div className="flex items-center justify-between text-xs text-muted-foreground font-medium">
                     <span>NSE:EQ</span>
                     <span className="flex items-center text-primary group-hover:underline">Details <ChevronRight className="w-3 h-3 ml-1" /></span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
