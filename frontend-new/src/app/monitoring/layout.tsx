import MainLayout from "@/components/layout/main-layout"

export default function MonitoringLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <MainLayout>
            {children}
        </MainLayout>
    )
}
