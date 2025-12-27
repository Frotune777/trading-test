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
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Sidebar flows naturally in flex container */}
            <div className="hidden md:block h-full border-r border-border bg-sidebar">
                <Sidebar />
            </div>
            {/* Main content takes remaining space */}
            <main className="flex-1 h-full overflow-y-auto bg-background">
                <Header />
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    )
}
