import { LayoutDashboard, TrendingUp, Database, Activity, BarChart3, Settings } from 'lucide-react';

export const navigation = [
    {
        title: 'Dashboard',
        href: '/settings/dashboard',
        icon: LayoutDashboard,
    },
    {
        title: 'Trading',
        icon: TrendingUp,
        children: [
            { title: 'Screener', href: '/trading/screener' },
            { title: 'Strategies', href: '/trading/strategies' },
        ],
    },
    {
        title: 'Data',
        icon: Database,
        children: [
            { title: 'Sources', href: '/data/sources' },
            { title: 'Management', href: '/data/management' },
            { title: 'Reconciliation', href: '/data/reconciliation' },
        ],
    },
    {
        title: 'Market',
        icon: BarChart3,
        children: [
            { title: 'Pulse', href: '/market/pulse' },
            { title: 'Stock', href: '/market/stock' },
            { title: 'Analytics', href: '/market/analytics' },
            { title: 'QUAD', href: '/market/quad' },
        ],
    },
    {
        title: 'Monitoring',
        icon: Activity,
        children: [
            { title: 'Dashboard', href: '/monitoring/dashboard' },
            { title: 'System', href: '/monitoring/system' },
            { title: 'Broker Health', href: '/monitoring/broker-health' },
            { title: 'Audit', href: '/monitoring/audit' },
        ],
    },
    {
        title: 'Settings',
        icon: Settings,
        children: [
            { title: 'API Keys', href: '/settings/api-keys' },
            { title: 'Sandbox', href: '/settings/sandbox' },
        ],
    },
];
