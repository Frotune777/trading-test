import { useEffect, useRef, useState } from 'react';

/**
 * Throttle hook - limits function execution to once per interval
 * Use for high-frequency updates like price tickers
 */
export function useThrottle<T>(value: T, interval: number = 500): T {
    const [throttledValue, setThrottledValue] = useState<T>(value);
    const lastExecuted = useRef<number>(Date.now());

    useEffect(() => {
        const now = Date.now();
        const timeSinceLastExecution = now - lastExecuted.current;

        if (timeSinceLastExecution >= interval) {
            lastExecuted.current = now;
            setThrottledValue(value);
        } else {
            const timerId = setTimeout(() => {
                lastExecuted.current = Date.now();
                setThrottledValue(value);
            }, interval - timeSinceLastExecution);

            return () => clearTimeout(timerId);
        }
    }, [value, interval]);

    return throttledValue;
}

export default useThrottle;
