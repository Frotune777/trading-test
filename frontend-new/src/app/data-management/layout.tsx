import MainLayout from "@/components/layout/main-layout"

export default function DataManagementLayout({
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
