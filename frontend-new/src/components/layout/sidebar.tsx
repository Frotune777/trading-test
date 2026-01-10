"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
    ChevronDown,
    ChevronRight,
    ChevronLeft,
} from "lucide-react"
import { useState, useEffect } from "react"
import { navigation } from "@/config/navigation"

export function Sidebar() {
    const pathname = usePathname()

    // State management for collapsible sections
    const [collapsed, setCollapsed] = useState(false)
    const [openSections, setOpenSections] = useState<Record<string, boolean>>({})

    // Load state from localStorage on mount
    useEffect(() => {
        const savedCollapsed = localStorage.getItem('sidebar-collapsed')
        const savedOpenSections = localStorage.getItem('sidebar-open-sections')

        if (savedCollapsed !== null) setCollapsed(savedCollapsed === 'true')
        if (savedOpenSections !== null) {
            try {
                setOpenSections(JSON.parse(savedOpenSections))
            } catch (e) {
                // Initialize all sections as open by default
                const initial: Record<string, boolean> = {}
                navigation.forEach(item => {
                    if (item.children) {
                        initial[item.title] = true
                    }
                })
                setOpenSections(initial)
            }
        } else {
            // Initialize all sections as open by default
            const initial: Record<string, boolean> = {}
            navigation.forEach(item => {
                if (item.children) {
                    initial[item.title] = true
                }
            })
            setOpenSections(initial)
        }
    }, [])

    const toggleCollapsed = () => {
        const newValue = !collapsed
        setCollapsed(newValue)
        localStorage.setItem('sidebar-collapsed', String(newValue))
    }

    const toggleSection = (title: string) => {
        const newOpenSections = {
            ...openSections,
            [title]: !openSections[title]
        }
        setOpenSections(newOpenSections)
        localStorage.setItem('sidebar-open-sections', JSON.stringify(newOpenSections))
    }

    return (
        <aside
            data-testid="sidebar"
            className={cn(
                "h-full bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-all duration-300 flex flex-col",
                collapsed ? "w-16" : "w-64"
            )}
        >
            {/* Header with collapse toggle */}
            <div className="p-3 border-b border-sidebar-border flex items-center justify-between">
                {!collapsed && (
                    <Link href="/settings/dashboard" className="flex items-center">
                        <div className="relative w-8 h-8 mr-3">
                            <div className="absolute inset-0 bg-primary/20 rounded-lg" />
                            <div className="absolute inset-2 bg-primary rounded-md" />
                        </div>
                        <h1 className="text-xl font-black tracking-tighter uppercase italic text-foreground">
                            Fortune
                        </h1>
                    </Link>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleCollapsed}
                    className="h-9 w-9"
                    title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                    data-testid="sidebar-toggle"
                >
                    {collapsed ? (
                        <ChevronRight className="h-5 w-5" />
                    ) : (
                        <ChevronLeft className="h-5 w-5" />
                    )}
                </Button>
            </div>

            {/* Scrollable content area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="p-3 space-y-2">
                    {navigation.map((item) => {
                        const Icon = item.icon
                        const isActive = item.href ? pathname === item.href : false

                        // Single link item (no children)
                        if (!item.children) {
                            return (
                                <Link
                                    key={item.title}
                                    href={item.href!}
                                    data-testid={`nav-link-${item.title.toLowerCase().replace(/\s+/g, '-')}`}
                                    className={cn(
                                        "flex items-center p-3 rounded-lg transition group",
                                        "hover:bg-sidebar-accent",
                                        isActive
                                            ? "bg-sidebar-accent text-sidebar-accent-foreground"
                                            : "text-muted-foreground"
                                    )}
                                    title={collapsed ? item.title : undefined}
                                >
                                    <Icon className="h-5 w-5 flex-shrink-0" />
                                    {!collapsed && <span className="ml-3 font-medium">{item.title}</span>}
                                </Link>
                            )
                        }

                        // Collapsible section with children
                        const isOpen = openSections[item.title] ?? true
                        const hasActiveChild = item.children.some(child => pathname === child.href)

                        return (
                            <div key={item.title} className="space-y-1">
                                <button
                                    onClick={() => toggleSection(item.title)}
                                    className={cn(
                                        "w-full flex items-center justify-between p-3 rounded-lg transition",
                                        "hover:bg-sidebar-accent",
                                        hasActiveChild ? "text-sidebar-accent-foreground" : "text-muted-foreground"
                                    )}
                                    title={collapsed ? item.title : undefined}
                                >
                                    <div className="flex items-center">
                                        <Icon className="h-5 w-5 flex-shrink-0" />
                                        {!collapsed && <span className="ml-3 font-medium">{item.title}</span>}
                                    </div>
                                    {!collapsed && (
                                        isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                                    )}
                                </button>
                                {isOpen && (
                                    <div className={cn("space-y-1", collapsed ? "" : "ml-4")}>
                                        {item.children.map((child) => {
                                            const isChildActive = pathname === child.href
                                            return (
                                                <Link
                                                    key={child.href}
                                                    href={child.href}
                                                    data-testid={`nav-link-${child.title.toLowerCase().replace(/\s+/g, '-')}`}
                                                    className={cn(
                                                        "flex items-center p-2 rounded-lg transition",
                                                        "hover:bg-sidebar-accent",
                                                        isChildActive
                                                            ? "bg-sidebar-accent text-sidebar-accent-foreground"
                                                            : "text-muted-foreground"
                                                    )}
                                                    title={collapsed ? child.title : undefined}
                                                >
                                                    {!collapsed && <span className="ml-3 text-sm">{child.title}</span>}
                                                </Link>
                                            )
                                        })}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
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
        </aside>
    )
}
