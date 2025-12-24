"use client"

import { Sidebar } from "./sidebar"
import { Header } from "./header"
import { ThemeProvider } from "../theme-provider"

export default function MainLayout({
    children
}: {
    children: React.ReactNode
}) {
    return (
        <ThemeProvider defaultTheme="dark" storageKey="trading-dashboard-theme">
            <div className="h-full relative bg-white dark:bg-slate-950">
                <div className="hidden h-full md:flex md:w-72 md:flex-col md:fixed md:inset-y-0 z-[80] bg-slate-100 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
                    <Sidebar />
                </div>
                <main className="md:pl-72 h-full bg-slate-50 dark:bg-slate-950 min-h-screen">
                    <Header />
                    <div className="p-8">
                        {children}
                    </div>
                </main>
            </div>
        </ThemeProvider>
    )
}
