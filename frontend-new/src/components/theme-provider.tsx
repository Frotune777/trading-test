"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"

type Theme = "dark" | "light"

interface ThemeProviderProps {
    children: React.ReactNode
    defaultTheme?: Theme
    storageKey?: string
}

interface ThemeProviderState {
    theme: Theme
    setTheme: (theme: Theme) => void
}

const ThemeProviderContext = React.createContext<ThemeProviderState | undefined>(undefined)

export function ThemeProvider({
    children,
    defaultTheme = "dark",
    storageKey = "trading-dashboard-theme",
    ...props
}: ThemeProviderProps) {
    const [theme, setTheme] = React.useState<Theme>(
        () => (typeof window !== "undefined" && (localStorage.getItem(storageKey) as Theme)) || defaultTheme
    )

    React.useEffect(() => {
        const root = window.document.documentElement
        root.classList.remove("light", "dark")
        root.classList.add(theme)
    }, [theme])

    const value = {
        theme,
        setTheme: (theme: Theme) => {
            localStorage.setItem(storageKey, theme)
            setTheme(theme)
        },
    }

    return (
        <ThemeProviderContext.Provider {...props} value={value}>
            {children}
        </ThemeProviderContext.Provider>
    )
}

export const useTheme = () => {
    const context = React.useContext(ThemeProviderContext)

    if (context === undefined)
        throw new Error("useTheme must be used within a ThemeProvider")

    return context
}

export function ThemeToggle() {
    const { theme, setTheme } = useTheme()

    return (
        <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="group relative inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
            aria-label="Toggle theme"
        >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0 text-amber-500" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100 text-sky-400" />
        </button>
    )
}
