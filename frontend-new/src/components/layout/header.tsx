"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "../theme-provider"

export function Header() {
    return (
        <div className="border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-950/50 backdrop-blur-xl p-4 sticky top-0 z-50">
            <div className="flex items-center justify-between">
                <div className="w-full max-w-xl relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-400" />
                    <Input
                        placeholder="Search stocks, ETFs, indices... (Press '/')"
                        className="pl-10 bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 focus:ring-slate-300 dark:focus:ring-slate-700 text-slate-900 dark:text-slate-200"
                    />
                </div>
                <div className="flex items-center gap-x-4">
                    <ThemeToggle />
                    <Button variant="ghost" className="text-sm font-medium text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">
                        Feedback
                    </Button>
                    <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-sky-500 to-blue-600" />
                </div>
            </div>
        </div>
    )
}
