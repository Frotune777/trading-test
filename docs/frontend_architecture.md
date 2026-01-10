# Frontend Architecture - QUAD Trading Platform

**Last Updated**: 2026-01-10  
**Framework**: Next.js 16.1.0 (App Router with Turbopack)  
**Language**: TypeScript  
**Styling**: Tailwind CSS 4 + Shadcn/UI  
**State Management**: React Query (TanStack Query)

---

## 📁 Project Structure

```
frontend-new/
├── src/
│   ├── app/                          # Next.js App Router pages
│   │   ├── layout.tsx                # Root layout (Providers, Toaster)
│   │   ├── page.tsx                  # Home page (redirects to /dashboard)
│   │   ├── globals.css               # Global styles + Tailwind
│   │   │
│   │   ├── dashboard/                # Main dashboard section
│   │   │   ├── layout.tsx            # Dashboard layout (MainLayout wrapper)
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── analysis/             # Stock analysis page
│   │   │   ├── derivatives/          # Derivatives analysis
│   │   │   ├── insider/              # Insider trading data
│   │   │   ├── quad-analytics/       # QUAD reasoning engine UI
│   │   │   ├── screener/             # Stock screener
│   │   │   └── settings/             # User settings
│   │   │
│   │   ├── analytics/                # Execution analytics (broker performance)
│   │   ├── api-keys/                 # API key management
│   │   ├── audit/                    # Audit logs
│   │   ├── broker-health/            # Broker health monitoring
│   │   ├── data-management/          # Data management tools
│   │   ├── data-source/              # Data ingestion configuration
│   │   ├── login/                    # Login page
│   │   ├── market-pulse/             # Market overview
│   │   ├── monitoring/               # System monitoring
│   │   ├── quad/                     # QUAD analysis (standalone)
│   │   ├── reconciliation/           # Position reconciliation
│   │   ├── register/                 # User registration
│   │   ├── sandbox/                  # Testing sandbox
│   │   ├── screener/                 # PKScreener integration
│   │   ├── stock/                    # Stock details
│   │   │   ├── [symbol]/             # Dynamic stock page
│   │   │   └── page.tsx              # Stock list
│   │   ├── strategies/               # Trading strategies
│   │   │   ├── [id]/                 # Strategy details
│   │   │   └── page.tsx              # Strategy list
│   │   └── ta-aggregator/            # Technical analysis aggregator
│   │
│   ├── components/                   # React components
│   │   ├── layout/                   # Layout components
│   │   │   ├── main-layout.tsx       # Main app layout (Sidebar + Header + Content)
│   │   │   ├── sidebar.tsx           # Navigation sidebar
│   │   │   └── header.tsx            # Top header bar
│   │   ├── quad/                     # QUAD-specific components
│   │   │   ├── conviction-timeline.tsx
│   │   │   ├── pillar-drift.tsx
│   │   │   └── decision-history.tsx
│   │   ├── monitoring/               # Monitoring components
│   │   ├── ui/                       # Shadcn/UI components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── toaster.tsx
│   │   │   └── ... (40+ components)
│   │   ├── providers.tsx             # React Query + Theme providers
│   │   └── theme-provider.tsx        # Dark/Light theme
│   │
│   ├── lib/                          # Utility libraries
│   │   ├── api/                      # API client functions
│   │   │   ├── production-api.ts     # Production API calls
│   │   │   └── index.ts              # Axios instance
│   │   └── utils.ts                  # Utility functions
│   │
│   └── types/                        # TypeScript types
│       ├── production.ts             # Production types
│       └── index.ts                  # Common types
│
├── public/                           # Static assets
├── package.json                      # Dependencies
├── tsconfig.json                     # TypeScript config
├── tailwind.config.ts                # Tailwind config
├── next.config.js                    # Next.js config
└── Dockerfile                        # Docker build config
```

---

## 🎨 Design System

### Layout Architecture

**Root Layout** (`app/layout.tsx`):
- Wraps entire app with `<Providers>` (React Query + Theme)
- Adds `<Toaster>` for notifications
- Sets global HTML/body classes

**Main Layout** (`components/layout/main-layout.tsx`):
- **Structure**: Flex container with sidebar + main content
- **Sidebar**: Hidden on mobile (`md:block`), fixed width
- **Content Area**: Flex-1, scrollable, with Header + page content
- **Padding**: Responsive `p-6 md:p-8 lg:p-10`
- **Max Width**: `max-w-[1600px]` for readability

**Page Layouts**: Each section (dashboard, analytics, etc.) has its own `layout.tsx` that wraps children in `<MainLayout>`

### Styling Conventions

```typescript
// Semantic color tokens (auto dark mode)
bg-background          // Main background
bg-card               // Card backgrounds
bg-sidebar            // Sidebar background
text-foreground       // Main text
text-muted-foreground // Secondary text
border-border         // Borders

// Spacing scale
space-y-8            // Vertical spacing between sections
p-6 md:p-8 lg:p-10   // Responsive padding
gap-3, gap-4         // Grid/flex gaps

// Container widths
container mx-auto    // Centered container
max-w-7xl           // 1280px max
max-w-[1600px]      // Custom 1600px max
```

---

## 🔌 API Integration

### API Client (`lib/api/index.ts`)

```typescript
import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### React Query Pattern

```typescript
// Fetching data
const { data, isLoading, error } = useQuery({
  queryKey: ['stocks'],
  queryFn: async () => {
    const response = await api.get('/data/stocks');
    return response.data;
  },
});

// Mutations
const mutation = useMutation({
  mutationFn: async (data) => {
    return api.post('/endpoint', data);
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['stocks'] });
  },
});
```

---

## 📄 Page Types & Patterns

### 1. Dashboard Pages (with MainLayout)

**Pattern**: Layout wrapper provides MainLayout
```typescript
// app/dashboard/layout.tsx
import MainLayout from '@/components/layout/main-layout';

export default function DashboardLayout({ children }) {
  return <MainLayout>{children}</MainLayout>;
}

// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <div className="container mx-auto max-w-7xl space-y-8">
      {/* Content - NO MainLayout wrapper here */}
    </div>
  );
}
```

### 2. Standalone Pages (with own layout)

**Pattern**: Page has its own layout.tsx
```typescript
// app/data-source/layout.tsx
import MainLayout from '@/components/layout/main-layout';

export default function DataSourceLayout({ children }) {
  return <MainLayout>{children}</MainLayout>;
}

// app/data-source/page.tsx
export default function DataSourcePage() {
  return (
    <div className="container mx-auto max-w-7xl space-y-8">
      {/* Content */}
    </div>
  );
}
```

### 3. Auth Pages (no MainLayout)

**Pattern**: No layout wrapper
```typescript
// app/login/page.tsx
export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      {/* Login form */}
    </div>
  );
}
```

---

## 🧩 Key Components

### QUAD Analytics Components

**ConvictionTimeline** (`components/quad/conviction-timeline.tsx`):
- Displays conviction score over time
- Props: `symbol: string`, `days: number`
- API: `GET /api/v1/quad-analytics/conviction-timeline`

**PillarDrift** (`components/quad/pillar-drift.tsx`):
- Shows how each pillar (Trend, Momentum, etc.) changes
- Props: `symbol: string`
- API: `GET /api/v1/quad-analytics/pillar-drift`

**DecisionHistory** (`components/quad/decision-history.tsx`):
- Table of past QUAD decisions
- Props: `symbol: string`, `limit: number`
- API: `GET /api/v1/quad-analytics/decisions`

### Layout Components

**Sidebar** (`components/layout/sidebar.tsx`):
- Navigation menu with icons
- Collapsible sections (Trading, Advanced, etc.)
- Active route highlighting

**Header** (`components/layout/header.tsx`):
- Search bar
- Symbol selector
- Theme toggle
- User menu

---

## 🚀 Key Features by Page

### `/dashboard/quad-analytics`
- **Purpose**: QUAD reasoning engine visualization
- **Components**: ConvictionTimeline, PillarDrift, DecisionHistory
- **API Endpoints**: 
  - `/quad-analytics/conviction-timeline`
  - `/quad-analytics/pillar-drift`
  - `/quad-analytics/decisions`

### `/screener`
- **Purpose**: PKScreener integration
- **Features**: Strategy selection, scan execution, results table
- **API Endpoints**:
  - `POST /screener/scan`
  - `GET /screener/status/{task_id}`
  - `GET /screener/results/latest`

### `/analytics`
- **Purpose**: Broker execution analytics
- **Features**: Latency, slippage, fill rate metrics
- **API Endpoints**:
  - `GET /production/broker-analytics/{broker}`

### `/data-source`
- **Purpose**: Manual data ingestion
- **Features**: Symbol selection, date range, interval config
- **API Endpoints**:
  - `GET /data/stocks`
  - `POST /data/ingest`
  - `GET /data/availability/{symbol}`

### `/monitoring`
- **Purpose**: System health monitoring
- **Features**: Latency tracking, traffic stats, error logs
- **API Endpoints**:
  - `GET /monitoring/health`
  - `GET /monitoring/latency`
  - `GET /monitoring/traffic`

---

## 🎯 Common Patterns

### Error Handling

```typescript
const { data, error } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
});

if (error) {
  return (
    <div className="text-red-600">
      Error: {error.message}
    </div>
  );
}
```

### Loading States

```typescript
if (isLoading) {
  return (
    <div className="flex items-center justify-center p-8">
      <RefreshCw className="w-6 h-6 animate-spin" />
    </div>
  );
}
```

### Responsive Design

```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Cards */}
</div>
```

---

## 🔧 Configuration Files

### `package.json` (Key Dependencies)
```json
{
  "dependencies": {
    "next": "16.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.62.11",
    "axios": "^1.7.9",
    "tailwindcss": "^4.0.0",
    "lucide-react": "^0.469.0",
    "recharts": "^2.15.0"
  }
}
```

### `tailwind.config.ts`
- Custom color scheme (background, foreground, card, etc.)
- Dark mode support (`class` strategy)
- Custom animations

### `next.config.js`
```javascript
module.exports = {
  output: 'standalone',  // For Docker
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};
```

---

## 📊 Data Flow

```
User Interaction
    ↓
React Component
    ↓
React Query (useQuery/useMutation)
    ↓
API Client (axios)
    ↓
Backend API (http://localhost:8000/api/v1)
    ↓
Response
    ↓
React Query Cache
    ↓
Component Re-render
```

---

## 🐛 Common Issues & Solutions

### Issue: Duplicate Sidebar
**Cause**: Page component wraps content in `<MainLayout>` when layout.tsx already provides it  
**Solution**: Remove `<MainLayout>` from page component, only use in layout.tsx

### Issue: Cramped Layout
**Cause**: Nested padding (p-6 inside p-8)  
**Solution**: Use `container mx-auto max-w-7xl` in page, let MainLayout handle padding

### Issue: API Connection Failed
**Cause**: Backend not running or wrong URL  
**Solution**: Check `NEXT_PUBLIC_API_URL` env var, verify backend is on port 8000

### Issue: Dark Mode Not Working
**Cause**: Missing ThemeProvider  
**Solution**: Ensure `<Providers>` wraps app in root layout.tsx

---

## 🚀 Development Workflow

### Local Development
```bash
cd frontend-new
npm install
npm run dev  # Runs on http://localhost:3000
```

### Docker Build
```bash
docker-compose build frontend
docker-compose up -d frontend  # Runs on http://localhost:3010
```

### Adding New Page
1. Create `app/new-page/page.tsx`
2. Create `app/new-page/layout.tsx` (if needs MainLayout)
3. Add route to sidebar navigation
4. Create API client functions in `lib/api/`
5. Add TypeScript types in `types/`

---

## 📝 Best Practices

1. **Always use layout.tsx for MainLayout** - Never wrap in page component
2. **Use semantic tokens** - `bg-card` not `bg-white dark:bg-gray-800`
3. **Responsive padding** - `p-6 md:p-8 lg:p-10`
4. **Container widths** - `max-w-7xl` or `max-w-[1600px]`
5. **React Query for all API calls** - Automatic caching, loading states
6. **TypeScript types** - Define interfaces for all API responses
7. **Error boundaries** - Handle errors gracefully
8. **Loading states** - Show spinners during data fetch
9. **Accessibility** - Use semantic HTML, ARIA labels
10. **Code splitting** - Use dynamic imports for heavy components

---

## 🔗 Related Documentation

- [Backend API Reference](./api_reference.md)
- [QUAD Reasoning Engine](./internal_architecture.md)
- [Database Schema](./database_schema.md)
- [Deployment Guide](./deployment.md)

---

**For LLM Context**: This document provides a complete overview of the frontend architecture. When making changes:
- Check if page has layout.tsx before adding MainLayout
- Use semantic color tokens for dark mode compatibility
- Follow responsive padding patterns (p-6 md:p-8 lg:p-10)
- Use React Query for all API interactions
- Maintain consistent spacing (space-y-8 for sections, gap-4 for grids)
