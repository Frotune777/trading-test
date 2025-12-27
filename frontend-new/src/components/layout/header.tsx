"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "../theme-provider"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useMarket } from "@/context/market-context"

export function Header() {
    const { symbol, setSymbol, timeframe, setTimeframe } = useMarket()

    return (
        <div className="border-b border-border bg-background/50 backdrop-blur-xl p-4 sticky top-0 z-50">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 w-full max-w-xl">
                    <div className="flex items-center gap-2">
                         <Select value={symbol} onValueChange={setSymbol}>
                            <SelectTrigger className="w-[180px] bg-muted/50 border-border">
                                <SelectValue placeholder="Select symbol" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="RELIANCE">RELIANCE</SelectItem>
                                <SelectItem value="TCS">TCS</SelectItem>
                                <SelectItem value="INFY">INFY</SelectItem>
                                <SelectItem value="HDFCBANK">HDFCBANK</SelectItem>
                                <SelectItem value="ICICIBANK">ICICIBANK</SelectItem>
                                <SelectItem value="SBIN">SBIN</SelectItem>
                                <SelectItem value="KOTAKBANK">KOTAKBANK</SelectItem>
                            </SelectContent>
                        </Select>
                        
                        <Select value={timeframe} onValueChange={setTimeframe}>
                             <SelectTrigger className="w-[100px] bg-muted/50 border-border">
                                <SelectValue placeholder="Timeframe" />
                            </SelectTrigger>
                             <SelectContent>
                                <SelectItem value="1m">1m</SelectItem>
                                <SelectItem value="5m">5m</SelectItem>
                                <SelectItem value="15m">15m</SelectItem>
                                <SelectItem value="1h">1h</SelectItem>
                                <SelectItem value="1d">1d</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-1">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search stocks..."
                                className="pl-10 bg-muted/50 border-border focus:ring-ring text-foreground"
                            />
                        </div>
                        <Button variant="default" className="bg-primary text-primary-foreground font-black text-xs uppercase tracking-widest px-6 h-10 border border-primary/20 shadow-[0_0_15px_rgba(var(--primary),0.3)] transition-all hover:scale-105 active:scale-95">
                            Search
                        </Button>
                    </div>
                </div>
                <div className="flex items-center gap-x-4">
                    <ThemeToggle />
                    <Button variant="outline" className="text-sm font-medium">
                        Feedback
                    </Button>
                    <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-sky-500 to-blue-600" />
                </div>
            </div>
        </div>
    )
}
