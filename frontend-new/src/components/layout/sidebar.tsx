"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
    LayoutDashboard,
    LineChart,
    BarChart3,
    PieChart,
    Settings,
    TrendingUp,
    Search,
    Brain,
    Activity,
    Shield,
    GitCompare,
    BarChart2,
    TestTube,
    Monitor,
    FileText,
    ChevronDown,
    ChevronRight,
    Database,
    ChevronLeft,
    Menu
} from "lucide-react"
import { useState, useEffect } from "react"

// Route groups
const coreRoutes = [
    {
        label: "Dashboard",
        icon: LayoutDashboard,
        href: "/dashboard",
        color: "text-sky-500",
    },
    {
        label: "Market Pulse",
        icon: LineChart,
        href: "/market-pulse",
        color: "text-emerald-500",
    },
    {
        label: "QUAD Analytics",
        icon: Brain,
        href: "/quad",
        color: "text-purple-500",
    },
]

const tradingRoutes = [
    {
        label: "Stock Analysis",
        icon: Search,
        href: "/stock",
        color: "text-blue-500",
    },
    {
        label: "Screener",
        icon: BarChart3,
        href: "/dashboard/screener",
        color: "text-violet-500",
    },
    {
        label: "Analysis",
        icon: LineChart,
        href: "/dashboard/analysis",
        color: "text-pink-700",
    },
    {
        label: "Derivatives",
        icon: TrendingUp,
        href: "/dashboard/derivatives",
        color: "text-orange-700",
    },
    {
        label: "Insider",
        icon: PieChart,
        href: "/dashboard/insider",
        color: "text-emerald-500",
    },
]

const advancedRoutes = [
    {
        label: "Strategies",
        icon: Activity,
        href: "/strategies",
        color: "text-blue-500",
    },
    {
        label: "Broker Health",
        icon: Shield,
        href: "/broker-health",
        color: "text-green-500",
    },
    {
        label: "Reconciliation",
        icon: GitCompare,
        href: "/reconciliation",
        color: "text-yellow-500",
    },
    {
        label: "Analytics",
        icon: BarChart2,
        href: "/analytics",
        color: "text-indigo-500",
    },
    {
        label: "Sandbox",
        icon: TestTube,
        href: "/sandbox",
        color: "text-pink-500",
    },
]

const systemRoutes = [
    {
        label: "Data Management",
        icon: Database,
        href: "/data-management",
        color: "text-teal-500",
    },
    {
        label: "Monitoring",
        icon: Monitor,
        href: "/monitoring",
        color: "text-cyan-500",
    },
    {
        label: "Audit Logs",
        icon: FileText,
        href: "/audit",
        color: "text-gray-500",
    },
]

export function Sidebar() {
    const pathname = usePathname()
    
    // Load initial state from localStorage
    const [collapsed, setCollapsed] = useState(false)
    const [tradingOpen, setTradingOpen] = useState(true)
    const [advancedOpen, setAdvancedOpen] = useState(false)
    const [systemOpen, setSystemOpen] = useState(false)

    // Load state from localStorage on mount
    useEffect(() => {
        const savedCollapsed = localStorage.getItem('sidebar-collapsed')
        const savedTradingOpen = localStorage.getItem('sidebar-trading-open')
        const savedAdvancedOpen = localStorage.getItem('sidebar-advanced-open')
        const savedSystemOpen = localStorage.getItem('sidebar-system-open')
        
        if (savedCollapsed !== null) setCollapsed(savedCollapsed === 'true')
        if (savedTradingOpen !== null) setTradingOpen(savedTradingOpen === 'true')
        if (savedAdvancedOpen !== null) setAdvancedOpen(savedAdvancedOpen === 'true')
        if (savedSystemOpen !== null) setSystemOpen(savedSystemOpen === 'true')
    }, [])

    // Save state to localStorage
    const toggleCollapsed = () => {
        const newValue = !collapsed
        setCollapsed(newValue)
        localStorage.setItem('sidebar-collapsed', String(newValue))
    }

    const toggleTrading = () => {
        const newValue = !tradingOpen
        setTradingOpen(newValue)
        localStorage.setItem('sidebar-trading-open', String(newValue))
    }

    const toggleAdvanced = () => {
        const newValue = !advancedOpen
        setAdvancedOpen(newValue)
        localStorage.setItem('sidebar-advanced-open', String(newValue))
    }

    const toggleSystem = () => {
        const newValue = !systemOpen
        setSystemOpen(newValue)
        localStorage.setItem('sidebar-system-open', String(newValue))
    }

    return (
        <div 
            className={cn(
                "h-full bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-all duration-300 flex flex-col",
                collapsed ? "w-16" : "w-64"
            )}
        >
            {/* Header with collapse toggle */}
            <div className="p-3 border-b border-sidebar-border flex items-center justify-between">
                {!collapsed && (
                    <Link href="/dashboard" className="flex items-center">
                        <div className="relative w-8 h-8 mr-3">
                            <div className="absolute inset-0 bg-primary/20 rounded-lg" />
                            <div className="absolute inset-2 bg-primary rounded-md" />
                        </div>
                        <h1 className="text-xl font-black tracking-tighter uppercase italic text-foreground">
                            Fortune
                        </h1>
                    </Link>
                )}
                <button
                    onClick={toggleCollapsed}
                    className="p-2 hover:bg-sidebar-accent rounded-lg transition"
                    title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {collapsed ? (
                        <ChevronRight className="h-5 w-5" />
                    ) : (
                        <ChevronLeft className="h-5 w-5" />
                    )}
                </button>
            </div>

            {/* Scrollable content area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="p-3 space-y-4">
                    {/* Core Routes - Always visible */}
                    <div className="space-y-1">
                        {!collapsed && (
                            <div className="px-3 mb-2">
                                <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    Core
                                </h2>
                            </div>
                        )}
                        {coreRoutes.map((route) => (
                            <Link
                                key={route.href}
                                href={route.href}
                                className={cn(
                                    "flex items-center p-3 rounded-lg transition group",
                                    "hover:bg-sidebar-accent",
                                    pathname === route.href 
                                        ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                                        : "text-muted-foreground"
                                )}
                                title={collapsed ? route.label : undefined}
                            >
                                <route.icon className={cn("h-5 w-5 flex-shrink-0", route.color)} />
                                {!collapsed && <span className="ml-3 font-medium">{route.label}</span>}
                            </Link>
                        ))}
                    </div>

                    {/* Trading Group */}
                    <div className="space-y-1">
                        <button
                            onClick={toggleTrading}
                            className="w-full flex items-center justify-between p-3 rounded-lg transition hover:bg-sidebar-accent text-muted-foreground"
                        >
                            <div className="flex items-center">
                                <TrendingUp className="h-5 w-5 flex-shrink-0" />
                                {!collapsed && <span className="ml-3 font-medium">Trading</span>}
                            </div>
                            {!collapsed && (
                                tradingOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                            )}
                        </button>
                        {tradingOpen && (
                            <div className={cn("space-y-1", collapsed ? "" : "ml-4")}>
                                {tradingRoutes.map((route) => (
                                    <Link
                                        key={route.href}
                                        href={route.href}
                                        className={cn(
                                            "flex items-center p-2 rounded-lg transition",
                                            "hover:bg-sidebar-accent",
                                            pathname === route.href 
                                                ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                                                : "text-muted-foreground"
                                        )}
                                        title={collapsed ? route.label : undefined}
                                    >
                                        <route.icon className={cn("h-4 w-4 flex-shrink-0", route.color)} />
                                        {!collapsed && <span className="ml-3 text-sm">{route.label}</span>}
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Advanced Group */}
                    <div className="space-y-1">
                        <button
                            onClick={toggleAdvanced}
                            className="w-full flex items-center justify-between p-3 rounded-lg transition hover:bg-sidebar-accent text-muted-foreground"
                        >
                            <div className="flex items-center">
                                <Activity className="h-5 w-5 flex-shrink-0" />
                                {!collapsed && (
                                    <div className="flex items-center ml-3">
                                        <span className="font-medium">Advanced</span>
                                        <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                                            Phase 8
                                        </span>
                                    </div>
                                )}
                            </div>
                            {!collapsed && (
                                advancedOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                            )}
                        </button>
                        {advancedOpen && (
                            <div className={cn("space-y-1", collapsed ? "" : "ml-4")}>
                                {advancedRoutes.map((route) => (
                                    <Link
                                        key={route.href}
                                        href={route.href}
                                        className={cn(
                                            "flex items-center p-2 rounded-lg transition",
                                            "hover:bg-sidebar-accent",
                                            pathname === route.href 
                                                ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                                                : "text-muted-foreground"
                                        )}
                                        title={collapsed ? route.label : undefined}
                                    >
                                        <route.icon className={cn("h-4 w-4 flex-shrink-0", route.color)} />
                                        {!collapsed && <span className="ml-3 text-sm">{route.label}</span>}
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* System Group */}
                    <div className="space-y-1">
                        <button
                            onClick={toggleSystem}
                            className="w-full flex items-center justify-between p-3 rounded-lg transition hover:bg-sidebar-accent text-muted-foreground"
                        >
                            <div className="flex items-center">
                                <Monitor className="h-5 w-5 flex-shrink-0" />
                                {!collapsed && <span className="ml-3 font-medium">System</span>}
                            </div>
                            {!collapsed && (
                                systemOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                            )}
                        </button>
                        {systemOpen && (
                            <div className={cn("space-y-1", collapsed ? "" : "ml-4")}>
                                {systemRoutes.map((route) => (
                                    <Link
                                        key={route.href}
                                        href={route.href}
                                        className={cn(
                                            "flex items-center p-2 rounded-lg transition",
                                            "hover:bg-sidebar-accent",
                                            pathname === route.href 
                                                ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                                                : "text-muted-foreground"
                                        )}
                                        title={collapsed ? route.label : undefined}
                                    >
                                        <route.icon className={cn("h-4 w-4 flex-shrink-0", route.color)} />
                                        {!collapsed && <span className="ml-3 text-sm">{route.label}</span>}
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Settings at bottom */}
            <div className="p-3 border-t border-sidebar-border">
                <Link
                    href="/dashboard/settings"
                    className={cn(
                        "flex items-center p-3 rounded-lg transition",
                        "hover:bg-sidebar-accent",
                        pathname === "/dashboard/settings" 
                            ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                            : "text-muted-foreground"
                    )}
                    title={collapsed ? "Settings" : undefined}
                >
                    <Settings className="h-5 w-5 flex-shrink-0" />
                    {!collapsed && <span className="ml-3 font-medium">Settings</span>}
                </Link>
            </div>

            {/* Custom scrollbar styles */}
            <style jsx global>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(148, 163, 184, 0.3);
                    border-radius: 3px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(148, 163, 184, 0.5);
                }
                .dark .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(148, 163, 184, 0.2);
                }
                .dark .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(148, 163, 184, 0.4);
                }
            `}</style>
        </div>
    )
}
