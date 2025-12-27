import MainLayout from "@/components/layout/main-layout"

export default function ReconciliationLayout({
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
