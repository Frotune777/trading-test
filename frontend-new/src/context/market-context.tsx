"use client"

import React, { createContext, useContext, useState, useEffect } from "react"

interface MarketContextType {
    symbol: string
    timeframe: string
    setSymbol: (symbol: string) => void
    setTimeframe: (timeframe: string) => void
}

const MarketContext = createContext<MarketContextType | undefined>(undefined)

export function MarketProvider({ children }: { children: React.ReactNode }) {
    // Initialize from localStorage if available, otherwise default
    const [symbol, setSymbolState] = useState("RELIANCE")
    const [timeframe, setTimeframeState] = useState("1D")

    useEffect(() => {
        const savedSymbol = localStorage.getItem("market-symbol")
        const savedTimeframe = localStorage.getItem("market-timeframe")
        if (savedSymbol) setSymbolState(savedSymbol)
        if (savedTimeframe) setTimeframeState(savedTimeframe)
    }, [])

    const setSymbol = (newSymbol: string) => {
        setSymbolState(newSymbol)
        localStorage.setItem("market-symbol", newSymbol)
    }

    const setTimeframe = (newTimeframe: string) => {
        setTimeframeState(newTimeframe)
        localStorage.setItem("market-timeframe", newTimeframe)
    }

    return (
        <MarketContext.Provider value={{ symbol, timeframe, setSymbol, setTimeframe }}>
            {children}
        </MarketContext.Provider>
    )
}

export function useMarket() {
    const context = useContext(MarketContext)
    if (context === undefined) {
        throw new Error("useMarket must be used within a MarketProvider")
    }
    return context
}
