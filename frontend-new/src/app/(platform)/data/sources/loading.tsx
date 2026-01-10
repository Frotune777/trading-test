import { Skeleton } from '@/components/ui/skeleton';

export default function DataSourceLoading() {
    return (
        <div className="container mx-auto max-w-7xl space-y-8">
            {/* Header */}
            <div className="space-y-2">
                <Skeleton className="h-10 w-80" />
                <Skeleton className="h-4 w-96" />
            </div>

            {/* Info Banner */}
            <Skeleton className="h-24 w-full rounded-lg" />

            {/* Symbol Selection */}
            <div className="bg-card rounded-lg border p-6 space-y-4">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="h-10 w-full" />
            </div>

            {/* Data Parameters */}
            <div className="bg-card rounded-lg border p-6 space-y-4">
                <Skeleton className="h-6 w-40" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                </div>
                <Skeleton className="h-10 w-full md:w-auto" />
            </div>
        </div>
    );
}
