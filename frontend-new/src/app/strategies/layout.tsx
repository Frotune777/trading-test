import MainLayout from "@/components/layout/main-layout"

export default function StrategiesLayout({
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
