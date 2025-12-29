# Data Source Configuration Page - Implementation Guide

## Overview

**Purpose**: Replace yfinance with NSE data ingestion  
**Location**: `/app/data-source/page.tsx`  
**Backend Endpoint**: `POST /api/v1/data/ingest`  
**Priority**: HIGH (Critical for data pipeline)

---

## Backend API Integration

### Available Endpoints

```typescript
// 1. Ingest Market Data
POST /api/v1/data/ingest
Query Params:
  - symbols: string[] (e.g., ["RELIANCE", "TCS"])
  - from: string (YYYY-MM-DD)
  - to: string (YYYY-MM-DD)
  - interval: string (1d, 1h, 15m, etc.)

Response:
{
  "status": "success",
  "symbols_processed": 2,
  "records_inserted": 500,
  "message": "Data ingestion completed"
}

// 2. Check Data Availability
GET /api/v1/data/availability/{symbol}
Response:
{
  "symbol": "RELIANCE",
  "available": true,
  "last_update": "2025-01-30T10:30:00Z",
  "record_count": 1000,
  "date_range": {
    "from": "2024-01-01",
    "to": "2025-01-30"
  }
}

// 3. List Available Stocks
GET /api/v1/data/stocks
Response:
{
  "stocks": [
    { "symbol": "RELIANCE", "name": "Reliance Industries Ltd" },
    { "symbol": "TCS", "name": "Tata Consultancy Services" }
  ]
}
```

---

## Page Structure

### File: `src/app/data-source/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Select } from '@/components/ui/select';
import { toast } from 'react-hot-toast';
import { apiClient } from '@/lib/api/client';

export default function DataSourcePage() {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    to: new Date(),
  });
  const [interval, setInterval] = useState('1d');

  // Fetch available stocks
  const { data: stocks } = useQuery({
    queryKey: ['stocks'],
    queryFn: async () => {
      const { data } = await apiClient.get('/data/stocks');
      return data.stocks;
    },
  });

  // Data ingestion mutation
  const ingestMutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post('/data/ingest', null, {
        params: {
          symbols: selectedSymbols.join(','),
          from: dateRange.from.toISOString().split('T')[0],
          to: dateRange.to.toISOString().split('T')[0],
          interval,
        },
      });
      return data;
    },
    onSuccess: (data) => {
      toast.success(`✅ Ingested ${data.records_inserted} records for ${data.symbols_processed} symbols`);
    },
    onError: (error) => {
      toast.error(`❌ Ingestion failed: ${error.message}`);
    },
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Data Source Configuration</h1>
      
      {/* Symbol Selection */}
      <div>
        <label>Select Symbols (NSE)</label>
        <MultiSelect
          options={stocks?.map(s => ({ value: s.symbol, label: s.name }))}
          value={selectedSymbols}
          onChange={setSelectedSymbols}
        />
      </div>

      {/* Date Range */}
      <div>
        <label>Date Range</label>
        <DateRangePicker
          from={dateRange.from}
          to={dateRange.to}
          onChange={setDateRange}
        />
      </div>

      {/* Interval */}
      <div>
        <label>Interval</label>
        <Select
          value={interval}
          onChange={setInterval}
          options={[
            { value: '1d', label: 'Daily' },
            { value: '1h', label: 'Hourly' },
            { value: '15m', label: '15 Minutes' },
          ]}
        />
      </div>

      {/* Ingest Button */}
      <Button
        onClick={() => ingestMutation.mutate()}
        disabled={ingestMutation.isPending || selectedSymbols.length === 0}
      >
        {ingestMutation.isPending ? 'Ingesting...' : 'Ingest Data'}
      </Button>

      {/* Data Availability Table */}
      <DataAvailabilityTable symbols={selectedSymbols} />
    </div>
  );
}
```

---

## Components to Create

### 1. Symbol Multi-Select

```typescript
// src/components/data-source/SymbolMultiSelect.tsx
import { useState } from 'react';
import { Command, CommandInput, CommandList, CommandItem } from '@/components/ui/command';

interface SymbolMultiSelectProps {
  options: { value: string; label: string }[];
  value: string[];
  onChange: (value: string[]) => void;
}

export function SymbolMultiSelect({ options, value, onChange }: SymbolMultiSelectProps) {
  const [search, setSearch] = useState('');

  const filteredOptions = options.filter(opt =>
    opt.label.toLowerCase().includes(search.toLowerCase()) ||
    opt.value.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Command>
      <CommandInput
        placeholder="Search symbols..."
        value={search}
        onValueChange={setSearch}
      />
      <CommandList>
        {filteredOptions.map(opt => (
          <CommandItem
            key={opt.value}
            onSelect={() => {
              if (value.includes(opt.value)) {
                onChange(value.filter(v => v !== opt.value));
              } else {
                onChange([...value, opt.value]);
              }
            }}
          >
            <input
              type="checkbox"
              checked={value.includes(opt.value)}
              readOnly
            />
            {opt.label} ({opt.value})
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  );
}
```

### 2. Data Availability Table

```typescript
// src/components/data-source/DataAvailabilityTable.tsx
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';

export function DataAvailabilityTable({ symbols }: { symbols: string[] }) {
  const { data: availability } = useQuery({
    queryKey: ['data-availability', symbols],
    queryFn: async () => {
      const results = await Promise.all(
        symbols.map(async (symbol) => {
          const { data } = await apiClient.get(`/data/availability/${symbol}`);
          return data;
        })
      );
      return results;
    },
    enabled: symbols.length > 0,
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Last Update</TableHead>
          <TableHead>Records</TableHead>
          <TableHead>Date Range</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {availability?.map(item => (
          <TableRow key={item.symbol}>
            <TableCell>{item.symbol}</TableCell>
            <TableCell>
              {item.available ? (
                <span className="text-green-600">✓ Available</span>
              ) : (
                <span className="text-red-600">✗ Not Available</span>
              )}
            </TableCell>
            <TableCell>{new Date(item.last_update).toLocaleString()}</TableCell>
            <TableCell>{item.record_count}</TableCell>
            <TableCell>
              {item.date_range.from} → {item.date_range.to}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### 3. Bulk Ingestion Progress

```typescript
// src/components/data-source/BulkIngestionProgress.tsx
import { Progress } from '@/components/ui/progress';

export function BulkIngestionProgress({ current, total }: { current: number; total: number }) {
  const percentage = (current / total) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Ingesting data...</span>
        <span>{current} / {total} symbols</span>
      </div>
      <Progress value={percentage} />
    </div>
  );
}
```

---

## Integration with Existing Data Management Page

### Update: `src/app/data-management/page.tsx`

Add a link/button to the new Data Source Configuration page:

```typescript
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function DataManagementPage() {
  return (
    <div>
      <h1>Data Management</h1>
      
      {/* Add this button */}
      <Link href="/data-source">
        <Button>Configure Data Source (NSE)</Button>
      </Link>
      
      {/* Existing data management UI */}
    </div>
  );
}
```

---

## NSE Data Script Integration

### Backend Script Location
```
backend/app/data_sources/nse_complete.py
```

### How It Works
1. Frontend calls `POST /api/v1/data/ingest`
2. Backend uses NSE data scripts to fetch data
3. Data is stored in `PriceHistory` table
4. Frontend displays success/error status

---

## Testing Checklist

- [ ] Symbol selection works (multi-select)
- [ ] Date range picker functional
- [ ] Interval selection works
- [ ] Ingest button triggers API call
- [ ] Success toast shows on successful ingestion
- [ ] Error toast shows on failure
- [ ] Data availability table updates after ingestion
- [ ] Progress indicator shows during bulk ingestion
- [ ] Last update timestamp displays correctly

---

## Dependencies to Install

```bash
npm install react-day-picker
npm install cmdk  # For Command component
```

---

## Navigation Update

Add to sidebar navigation:

```typescript
// src/components/layout/sidebar.tsx
{
  name: 'Data Source',
  href: '/data-source',
  icon: DatabaseIcon,
}
```

---

## Success Criteria

✅ Users can select NSE symbols  
✅ Users can specify date range and interval  
✅ Data ingestion works via backend API  
✅ Data availability is visible  
✅ yfinance references are removed  
✅ NSE data pipeline is fully functional
