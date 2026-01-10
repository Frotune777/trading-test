import { Skeleton } from '@/components/ui/skeleton';

export default function AnalyticsLoading() {
    return (
        <div className="container mx-auto max-w-7xl space-y-8">
            {/* Header */}
            <Skeleton className="h-10 w-64" />

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-32 w-full rounded-lg" />
                ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton className="h-[350px] w-full rounded-lg" />
                <Skeleton className="h-[350px] w-full rounded-lg" />
            </div>

            {/* Table */}
            <Skeleton className="h-[400px] w-full rounded-lg" />
        </div>
    );
}
