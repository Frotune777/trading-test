import { Skeleton } from '@/components/ui/skeleton';

export default function MonitoringLoading() {
    return (
        <div className="container mx-auto max-w-7xl space-y-8">
            {/* Header */}
            <Skeleton className="h-10 w-64" />

            {/* Health Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-24 w-full rounded-lg" />
                ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton className="h-[300px] w-full rounded-lg" />
                <Skeleton className="h-[300px] w-full rounded-lg" />
            </div>

            {/* Logs */}
            <Skeleton className="h-[400px] w-full rounded-lg" />
        </div>
    );
}
