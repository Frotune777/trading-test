# Fortune Trading Frontend (Next.js 14)

The modern React frontend for the Fortune Trading Platform, built with Next.js 14 (App Router), Tailwind CSS, and Shadcn/UI.

## 🏗️ Architecture Overview

This project follows the **Next.js 14 App Router** paradigm with a focus on component modularity and global state management.

### Key Components

-   **Global Market State**:
    -   Managed via `src/context/market-context.tsx`.
    -   Provides global access to `symbol` and `timeframe` across the application.
    -   **Usage**: `const { symbol, setSymbol } = useMarket()`
    -   **Persistence**: Automatically persists to `localStorage`.

-   **Layout System**:
    -   **Root Layout** (`app/layout.tsx`): Handles global providers (`QueryClient`, `MarketProvider`) and HTML structure.
    -   **Main Layout** (`components/layout/main-layout.tsx`): The primary application shell containing the **Sidebar** and **Header**.
    -   **Usage Rule**: Route layouts (e.g., `app/quad/layout.tsx`) should wrap their children in `<MainLayout>` to ensure consistent navigation. Avoid reusing `MainLayout` inside pages (`page.tsx`) to prevent duplicate sidebars.

-   **QUAD Analytics Module**:
    -   Located in `app/quad/`.
    -   Integrates with the Institutional QUAD v2 backend.
    -   Uses `useQuadAnalytics` hook for data fetching.
    -   Visualizes 6-pillar analysis using isolated components (`PillarContribution`, `ConvictionTimeline`, etc.).

## 📂 Directory Structure

```
src/
├── app/                 # App Router Pages
│   ├── layout.tsx       # Root Layout (Providers)
│   ├── quad/            # QUAD Analytics Module
│   ├── stock/           # Stock Analysis Module
│   └── ...
├── components/          # React Components
│   ├── layout/          # Layout components (Sidebar, Header, MainLayout)
│   ├── quad/            # QUAD-specific visualizations
│   ├── ui/              # Shadcn/UI primitives
│   └── providers.tsx    # Global Provider wrapper
├── context/             # React Contexts (MarketContext)
├── hooks/               # Custom React Hooks
└── lib/                 # Utilities and API clients
```

## 🚀 Development

### Prerequisites

-   Node.js 20+
-   Backend services running (via Docker)

### Running Locally

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Visit [http://localhost:3010](http://localhost:3010) (mapped via Docker) or [http://localhost:3000](http://localhost:3000) (if running locally without Docker mapping).

## 🛠️ Common Patterns

### Adding a New Page inside the Dashboard

1.  Create a folder: `app/my-new-page/`
2.  Create `page.tsx`:
    ```tsx
    export default function MyPage() {
      return <div>My Content</div>
    }
    ```
3.  Create `layout.tsx`:
    ```tsx
    import MainLayout from "@/components/layout/main-layout"
    export default function Layout({ children }: { children: React.ReactNode }) {
      return <MainLayout>{children}</MainLayout>
    }
    ```

### Accessing Global Symbol

```tsx
import { useMarket } from "@/context/market-context"

export default function MyComponent() {
  const { symbol } = useMarket() // "RELIANCE", "TCS", etc.
  return <div>Current Symbol: {symbol}</div>
}
```
