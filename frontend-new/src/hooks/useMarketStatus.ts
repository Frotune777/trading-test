import { useCallback } from 'react'

export const useMarketStatus = () => {
    /**
     * Returns the refresh interval based on the category and current market status.
     * Defaulting to 10 seconds for market data and 60 seconds for others for now.
     */
    const refreshInterval = useCallback((category: 'market' | 'other' = 'market') => {
        // In a real implementation, this would check if the market is open
        // and adjust the interval accordingly (e.g., faster during market hours).
        return category === 'market' ? 10000 : 60000
    }, [])

    return {
        isMarketOpen: true, // Mock value
        refreshInterval,
        marketStatus: 'OPEN'
    }
}

export default useMarketStatus;
