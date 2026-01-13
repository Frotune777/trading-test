export default function MonitoringPage() {
    return (
        <div className="h-full w-full p-6 space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold tracking-tight">API Utilization Dashboard</h1>
                <p className="text-muted-foreground">
                    Real-time metrics for backend usage, latency, and error rates.
                </p>
            </div>

            {/* 
              We import the client-side component here.
              Ensure the path matches your project structure.
             */}
            <MonitoringDashboardWrapper />
        </div>
    );
}

import { MonitoringDashboard } from "@/components/monitoring/MonitoringDashboard";

function MonitoringDashboardWrapper() {
    return <MonitoringDashboard />;
}
