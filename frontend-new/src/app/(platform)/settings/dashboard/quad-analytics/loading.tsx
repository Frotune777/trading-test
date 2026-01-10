import { Skeleton } from '@/components/ui/skeleton';

export default function QuadAnalyticsLoading() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <Skeleton className="h-10 w-64" />
                <Skeleton className="h-10 w-48" />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-[300px] w-full" />
                </div>
                <div className="border rounded-lg p-6 space-y-4">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-[300px] w-full" />
                </div>
            </div>

            {/* Table */}
            <div className="border rounded-lg p-6 space-y-4">
                <Skeleton className="h-6 w-48" />
                <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <Skeleton key={i} className="h-16 w-full" />
                    ))}
                </div>
            </div>
        </div>
    );
}
