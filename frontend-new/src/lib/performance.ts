/**
 * Performance monitoring utilities for tracking page load metrics
 */

export function measurePerformance(metricName: string) {
    if (typeof window === 'undefined') return;

    const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            console.log(`[Performance] ${metricName}:`, {
                name: entry.name,
                duration: entry.duration,
                startTime: entry.startTime,
            });

            // Send to analytics service (future implementation)
            // sendToAnalytics(metricName, entry);
        }
    });

    observer.observe({ entryTypes: ['measure', 'navigation'] });
}

export function markPerformance(name: string) {
    if (typeof window === 'undefined') return;
    performance.mark(name);
}

export function measureBetween(startMark: string, endMark: string, measureName: string) {
    if (typeof window === 'undefined') return;

    try {
        performance.measure(measureName, startMark, endMark);
        const measure = performance.getEntriesByName(measureName)[0];
        console.log(`[Performance] ${measureName}: ${measure.duration.toFixed(2)}ms`);
    } catch (error) {
        console.error(`Failed to measure ${measureName}:`, error);
    }
}
