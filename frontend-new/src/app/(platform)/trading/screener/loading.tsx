import { Skeleton } from '@/components/ui/skeleton';

export default function ScreenerLoading() {
    return (
        <div className="container mx-auto max-w-7xl space-y-8">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-4 w-96" />
            </div>

            {/* Strategy Selection */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
            </div>

            {/* Results Table */}
            <div className="border rounded-lg p-6 space-y-4">
                <Skeleton className="h-6 w-40" />
                <div className="space-y-3">
                    {Array.from({ length: 10 }).map((_, i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                    ))}
                </div>
            </div>
        </div>
    );
}
