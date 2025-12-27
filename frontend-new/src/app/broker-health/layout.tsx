import MainLayout from "@/components/layout/main-layout"

export default function BrokerHealthLayout({
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
