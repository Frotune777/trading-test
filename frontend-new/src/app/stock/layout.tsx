import MainLayout from "@/components/layout/main-layout"

export default function StockLayout({
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
