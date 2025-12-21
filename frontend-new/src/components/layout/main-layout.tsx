"use client"

import { Sidebar } from "./sidebar"
import { Header } from "./header"

export default function MainLayout({
    children
}: {
    children: React.ReactNode
}) {
    return (
        <div className="h-full relative">
            <div className="hidden h-full md:flex md:w-72 md:flex-col md:fixed md:inset-y-0 z-[80] bg-slate-900">
                <Sidebar />
            </div>
            <main className="md:pl-72 h-full bg-slate-950 min-h-screen">
                <Header />
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    )
}
