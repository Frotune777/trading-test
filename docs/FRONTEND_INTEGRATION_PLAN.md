# Frontend Integration Plan: Existing Next.js App → Backend API

## Executive Summary

**Current State**: Next.js 14 app with 119 TypeScript files, existing QUAD components, TanStack Query  
**Target**: Full integration with backend API (200+ endpoints)  
**Approach**: Incremental integration leveraging existing components  
**Timeline**: 2-3 weeks

---

## 1. Current Frontend Analysis

### ✅ **What We Have**

**Tech Stack** (Already Configured):
- ✅ Next.js 14 (App Router)
- ✅ TypeScript
- ✅ TanStack Query v5
- ✅ Axios
- ✅ Shadcn/UI (Radix primitives)
- ✅ Recharts
- ✅ Tailwind CSS 4
- ✅ Playwright E2E tests

**Existing Pages**:
- ✅ `/dashboard` - Main dashboard
- ✅ `/quad` - QUAD Analytics
- ✅ `/strategies` - Strategy management
- ✅ `/monitoring` - System monitoring
- ✅ `/analytics` - Analytics dashboard
- ✅ `/reconciliation` - Position reconciliation
- ✅ `/sandbox` - Sandbox mode
- ✅ `/market-pulse` - Market data
- ✅ `/stock` - Stock analysis
- ✅ `/broker-health` - Broker health
- ✅ `/data-management` - Data management
- ✅ `/audit` - Audit logs

**Existing Components** (70+ components):
- ✅ `ConvictionMeter` - QUAD conviction gauge
- ✅ `PillarContribution` - Pillar visualization
- ✅ `ConvictionTimeline` - Timeline chart
- ✅ `BacktestResults` - Backtest visualization
- ✅ `AlertManager` - Alert management
- ✅ `PriceChart` - Price charts
- ✅ `MonitoringDashboard` - System health
- ✅ `TickerMarquee` - Market ticker
- ✅ And 60+ more...

**Global State**:
- ✅ `MarketContext` - Global symbol/timeframe state
- ✅ `QueryClient` - TanStack Query cache
- ✅ localStorage persistence

### ❌ **What's Missing**

**Critical Gaps**:
1. ❌ **Authentication System** - No login/register/API key management
2. ❌ **API Client Layer** - No typed API client for 200+ endpoints
3. ❌ **WebSocket Integration** - No real-time data connection
4. ❌ **Risk Control UI** - No kill switch, risk limits dashboard
5. ❌ **Execution Flow** - No order placement workflow
6. ❌ **Data Health Monitor** - No LTP freshness, price drift UI
7. ❌ **ML Prediction UI** - No shadow mode ML predictions
8. ❌ **Strategy DSL Editor** - No code editor for custom strategies
9. ❌ **Position Reconciliation** - Basic UI exists but needs backend integration
10. ❌ **Insider Sentinel** - No insider trading alerts

---

## 2. Integration Strategy

### Phase 1: Foundation (Week 1)

#### Task 1.1: API Client Setup ⭐
**Goal**: Create typed API client for all 200+ endpoints

**Files to Create**:
```
src/lib/api/
├── client.ts          # Axios instance with interceptors
├── auth.ts            # Authentication endpoints
├── quad.ts            # QUAD Analytics endpoints
├── strategy.ts        # Strategy management endpoints
├── market.ts          # Market data endpoints
├── risk.ts            # Risk control endpoints
├── execution.ts       # Order execution endpoints
├── monitoring.ts      # System monitoring endpoints
└── types.ts           # TypeScript interfaces
```

**Implementation**:
```typescript
// src/lib/api/client.ts
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key');
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

// Add error interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

#### Task 1.2: Authentication Pages ⭐
**Goal**: Add login, register, API key management

**Files to Create**:
```
src/app/
├── login/
│   └── page.tsx       # Login form
├── register/
│   └── page.tsx       # Registration form
└── api-keys/
    └── page.tsx       # API key management
```

**Implementation**:
```typescript
// src/app/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const { data } = await apiClient.post('/auth/login', {
        username,
        password,
      });
      
      // Generate API key
      const keyResponse = await apiClient.post('/auth/api-key/generate');
      localStorage.setItem('api_key', keyResponse.data.api_key);
      localStorage.setItem('user', JSON.stringify(data));
      
      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      {/* Login form UI */}
    </form>
  );
}
```

#### Task 1.3: WebSocket Manager ⭐
**Goal**: Set up real-time data connection

**Files to Create**:
```
src/lib/websocket/
├── manager.ts         # WebSocket connection manager
├── hooks.ts           # useWebSocket hook
└── types.ts           # WebSocket message types
```

**Implementation**:
```typescript
// src/lib/websocket/manager.ts
import ReconnectingWebSocket from 'reconnecting-websocket';

class WebSocketManager {
  private ws: ReconnectingWebSocket | null = null;
  private subscribers = new Map<string, Set<(data: any) => void>>();

  connect() {
    this.ws = new ReconnectingWebSocket('ws://localhost:8000/ws/market');
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const subscribers = this.subscribers.get(data.symbol) || new Set();
      subscribers.forEach(callback => callback(data));
    };
  }

  subscribe(symbol: string, callback: (data: any) => void) {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, new Set());
      this.ws?.send(JSON.stringify({ action: 'subscribe', symbols: [symbol] }));
    }
    this.subscribers.get(symbol)!.add(callback);
  }

  unsubscribe(symbol: string, callback: (data: any) => void) {
    this.subscribers.get(symbol)?.delete(callback);
    if (this.subscribers.get(symbol)?.size === 0) {
      this.ws?.send(JSON.stringify({ action: 'unsubscribe', symbols: [symbol] }));
    }
  }
}

export const wsManager = new WebSocketManager();
```

---

### Phase 2: Backend Integration (Week 2)

#### Task 2.1: Update Existing QUAD Components ⭐
**Goal**: Connect existing QUAD components to backend API

**Files to Modify**:
- `src/components/quad/ConvictionMeter.tsx` → Use `POST /quad-analytics/decision`
- `src/components/quad/ConvictionTimeline.tsx` → Use `GET /quad-analytics/{symbol}/timeline`
- `src/components/quad/BacktestResults.tsx` → Use `GET /quad-analytics/{symbol}/backtest`
- `src/components/quad/AlertManager.tsx` → Use `GET /quad-analytics/alerts`

**Example**:
```typescript
// src/components/quad/ConvictionMeter.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { quadApi } from '@/lib/api/quad';

export function ConvictionMeter({ symbol }: { symbol: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['quad-decision', symbol],
    queryFn: () => quadApi.getDecision(symbol, {
      quantitative_score: 85.5,
      universe_score: 72.3,
      alternative_score: 68.9,
      directional_score: 91.2,
    }),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>Conviction: {data?.conviction}%</h3>
      <p>Signal: {data?.signal}</p>
    </div>
  );
}
```

#### Task 2.2: Add Real-time Price Updates ⭐
**Goal**: Connect WebSocket to existing price components

**Files to Modify**:
- `src/components/market/TickerMarquee.tsx`
- `src/components/charts/PriceChart.tsx`
- `src/components/market/IndexSparklineCard.tsx`

**Example**:
```typescript
// src/components/market/TickerMarquee.tsx
'use client';

import { useEffect, useState } from 'react';
import { wsManager } from '@/lib/websocket/manager';

export function TickerMarquee() {
  const [prices, setPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    wsManager.connect();
    
    const symbols = ['RELIANCE', 'TCS', 'INFY'];
    symbols.forEach(symbol => {
      wsManager.subscribe(symbol, (data) => {
        setPrices(prev => ({ ...prev, [symbol]: data.ltp }));
      });
    });

    return () => {
      symbols.forEach(symbol => wsManager.unsubscribe(symbol, () => {}));
    };
  }, []);

  return (
    <div className="ticker-marquee">
      {Object.entries(prices).map(([symbol, price]) => (
        <span key={symbol}>{symbol}: ₹{price}</span>
      ))}
    </div>
  );
}
```

#### Task 2.3: Strategy Management Integration ⭐
**Goal**: Connect strategy pages to backend

**Files to Modify**:
- `src/app/strategies/page.tsx` → Use `GET /strategy`
- Add strategy creation modal → Use `POST /strategy`
- Add strategy toggle → Use `POST /strategy/{id}/toggle`

---

### Phase 3: New Features (Week 3)

#### Task 3.1: Risk Control Dashboard ⭐
**Goal**: Build comprehensive risk control UI

**Files to Create**:
```
src/app/risk-control/
├── page.tsx           # Risk dashboard
└── components/
    ├── KillSwitch.tsx
    ├── RiskLimits.tsx
    └── PositionMonitor.tsx
```

#### Task 3.2: Execution Workflow ⭐
**Goal**: Add order placement with dry-run confirmation

**Files to Create**:
```
src/components/execution/
├── OrderEntry.tsx     # Order entry modal
├── DryRunConfirm.tsx  # Dry-run confirmation
└── OrderHistory.tsx   # Order history table
```

#### Task 3.3: Data Health Monitor ⭐
**Goal**: Visualize data quality metrics

**Files to Create**:
```
src/app/data-health/
├── page.tsx
└── components/
    ├── LTPFreshness.tsx
    ├── PriceDrift.tsx
    └── FeedHealth.tsx
```

---

## 3. Implementation Checklist

### Week 1: Foundation ✅
- [ ] Create API client layer (`src/lib/api/`)
- [ ] Add authentication pages (login, register, API keys)
- [ ] Set up WebSocket manager
- [ ] Add environment variables (`.env.local`)
- [ ] Create auth context/hooks
- [ ] Add protected route wrapper

### Week 2: Integration ✅
- [ ] Connect QUAD components to backend
- [ ] Add real-time price updates via WebSocket
- [ ] Integrate strategy management
- [ ] Connect monitoring dashboard
- [ ] Add reconciliation backend calls
- [ ] Integrate analytics endpoints

### Week 3: New Features ✅
- [ ] Build risk control dashboard
- [ ] Add execution workflow (order entry + dry-run)
- [ ] Create data health monitor
- [ ] Add ML prediction UI (with shadow mode badge)
- [ ] Build insider sentinel alerts
- [ ] Add strategy DSL code editor

---

## 4. File Structure (After Integration)

```
frontend-new/
├── src/
│   ├── app/
│   │   ├── login/              # NEW
│   │   ├── register/           # NEW
│   │   ├── api-keys/           # NEW
│   │   ├── risk-control/       # NEW
│   │   ├── data-health/        # NEW
│   │   ├── execution/          # NEW
│   │   ├── dashboard/          # EXISTING (update)
│   │   ├── quad/               # EXISTING (update)
│   │   ├── strategies/         # EXISTING (update)
│   │   ├── monitoring/         # EXISTING (update)
│   │   └── ...
│   ├── lib/
│   │   ├── api/                # NEW
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── quad.ts
│   │   │   ├── strategy.ts
│   │   │   ├── market.ts
│   │   │   ├── risk.ts
│   │   │   └── types.ts
│   │   └── websocket/          # NEW
│   │       ├── manager.ts
│   │       └── hooks.ts
│   ├── context/
│   │   ├── market-context.tsx  # EXISTING
│   │   └── auth-context.tsx    # NEW
│   └── components/
│       ├── quad/               # EXISTING (update)
│       ├── execution/          # NEW
│       ├── risk/               # NEW
│       └── ...
└── .env.local                  # NEW
```

---

## 5. Environment Variables

Create `.env.local`:
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## 6. Quick Start Guide

### Step 1: Install Dependencies
```bash
cd frontend-new
npm install reconnecting-websocket
npm install @monaco-editor/react  # For strategy DSL editor
```

### Step 2: Create API Client
```bash
mkdir -p src/lib/api
# Create files as per Task 1.1
```

### Step 3: Add Authentication
```bash
mkdir -p src/app/login src/app/register src/app/api-keys
# Create files as per Task 1.2
```

### Step 4: Test Integration
```bash
npm run dev
# Visit http://localhost:3006
# Login → Generate API Key → Test QUAD Dashboard
```

---

## 7. Migration Priority

**High Priority** (Week 1):
1. API client layer
2. Authentication system
3. WebSocket integration
4. Update QUAD components

**Medium Priority** (Week 2):
5. Strategy management
6. Monitoring dashboard
7. Market data real-time updates

**Low Priority** (Week 3):
8. Risk control dashboard
9. Execution workflow
10. Data health monitor
11. Advanced features (ML, insider sentinel)

---

## 8. Testing Strategy

### Unit Tests
- Test API client functions
- Test WebSocket manager
- Test component data fetching

### E2E Tests (Playwright)
- Login flow
- QUAD decision workflow
- Strategy creation
- Order placement (dry-run)

### Integration Tests
- API endpoint connectivity
- WebSocket message handling
- Authentication flow

---

## 9. Success Criteria

- [ ] All existing pages connected to backend
- [ ] Real-time data updates via WebSocket
- [ ] Authentication fully functional
- [ ] QUAD workflow end-to-end working
- [ ] Risk controls operational
- [ ] Mobile responsive
- [ ] E2E tests passing

---

## 10. Next Steps

1. **Review this plan** with the team
2. **Create feature branches** for each phase
3. **Start with Phase 1** (API client + auth)
4. **Test incrementally** after each task
5. **Deploy to staging** after Week 2
6. **Production deployment** after Week 3

**Estimated Total Effort**: 120-150 hours (1 developer, 3 weeks)
