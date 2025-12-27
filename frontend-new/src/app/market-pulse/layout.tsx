import MainLayout from "@/components/layout/main-layout"

export default function MarketPulseLayout({
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
