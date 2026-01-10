'use client';

/**
 * Loading skeleton components for improved perceived performance
 */

interface SkeletonProps {
    className?: string;
    style?: React.CSSProperties;
}

export function Skeleton({ className = '', style }: SkeletonProps) {
    return (
        <div
            className={`animate-pulse bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 bg-[length:200%_100%] rounded ${className}`}
            style={{
                animation: 'shimmer 2s infinite linear',
                ...style,
            }}
        />
    );
}

export function CardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-8 w-8 rounded-full" />
            </div>
            <Skeleton className="h-12 w-24 mb-2" />
            <Skeleton className="h-4 w-48" />
        </div>
    );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="flex gap-4 p-4 border-b border-gray-200 dark:border-gray-700">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-5 w-28" />
            </div>

            {/* Rows */}
            {Array.from({ length: rows }).map((_, idx) => (
                <div key={idx} className="flex gap-4 p-4 border-b border-gray-100 dark:border-gray-800">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="h-4 w-28" />
                </div>
            ))}
        </div>
    );
}

export function ChartSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-6">
                <Skeleton className="h-6 w-40" />
                <div className="flex gap-2">
                    <Skeleton className="h-8 w-16 rounded-lg" />
                    <Skeleton className="h-8 w-16 rounded-lg" />
                    <Skeleton className="h-8 w-16 rounded-lg" />
                </div>
            </div>

            {/* Chart area */}
            <div className="relative h-80">
                {/* Y-axis labels */}
                <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between py-4">
                    {Array.from({ length: 5 }).map((_, idx) => (
                        <Skeleton key={idx} className="h-3 w-10" />
                    ))}
                </div>

                {/* Chart bars/lines */}
                <div className="ml-14 h-full flex items-end gap-2">
                    {Array.from({ length: 12 }).map((_, idx) => (
                        <Skeleton
                            key={idx}
                            className="flex-1"
                            style={{ height: `${Math.random() * 60 + 40}%` }}
                        />
                    ))}
                </div>

                {/* X-axis labels */}
                <div className="ml-14 mt-2 flex justify-between">
                    {Array.from({ length: 6 }).map((_, idx) => (
                        <Skeleton key={idx} className="h-3 w-12" />
                    ))}
                </div>
            </div>
        </div>
    );
}

export function DecisionCardSkeleton() {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <Skeleton className="h-7 w-32 mb-2" />
                    <Skeleton className="h-4 w-48" />
                </div>
                <Skeleton className="h-10 w-20 rounded-xl" />
            </div>

            <div className="grid grid-cols-4 gap-4 mb-4">
                {Array.from({ length: 4 }).map((_, idx) => (
                    <div key={idx}>
                        <Skeleton className="h-3 w-16 mb-2" />
                        <Skeleton className="h-8 w-full" />
                    </div>
                ))}
            </div>

            <div className="flex items-center gap-2">
                <Skeleton className="h-2 flex-1 rounded-full" />
                <Skeleton className="h-4 w-12" />
            </div>
        </div>
    );
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <Skeleton className="h-10 w-64" />
                <Skeleton className="h-10 w-32 rounded-xl" />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {Array.from({ length: 4 }).map((_, idx) => (
                    <CardSkeleton key={idx} />
                ))}
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartSkeleton />
                <ChartSkeleton />
            </div>

            {/* Table */}
            <TableSkeleton rows={8} />
        </div>
    );
}

// Add shimmer animation to global styles
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
    `;
    document.head.appendChild(style);
}

export default Skeleton;
