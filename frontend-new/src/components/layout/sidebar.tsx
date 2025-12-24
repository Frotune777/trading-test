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
    Brain
} from "lucide-react"

const routes = [
    {
        label: "Dashboard",
        icon: LayoutDashboard,
        href: "/dashboard",
        color: "text-sky-500",
    },
    {
        label: "QUAD Analytics",
        icon: Brain,
        href: "/quad",
        color: "text-purple-500",
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
    {
        label: "Settings",
        icon: Settings,
        href: "/dashboard/settings",
    },
]

export function Sidebar() {
    const pathname = usePathname()

    return (
        <div className="space-y-4 py-4 flex flex-col h-full bg-white dark:bg-slate-900 text-slate-900 dark:text-white border-r border-slate-200 dark:border-slate-800">
            <div className="px-3 py-2 flex-1">
                <Link href="/dashboard" className="flex items-center pl-3 mb-14">
                    <div className="relative w-8 h-8 mr-4">
                        <div className="absolute inset-0 bg-blue-600 rounded-lg opacity-20 animate-pulse" />
                        <div className="absolute inset-2 bg-blue-500 rounded-md" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                        Fortune Trading
                    </h1>
                </Link>
                <div className="space-y-1">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            className={cn(
                                "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition",
                                pathname === route.href ? "text-slate-900 dark:text-white bg-slate-100 dark:bg-white/10" : "text-slate-600 dark:text-zinc-400"
                            )}
                        >
                            <div className="flex items-center flex-1">
                                <route.icon className={cn("h-5 w-5 mr-3", route.color)} />
                                {route.label}
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    )
}
