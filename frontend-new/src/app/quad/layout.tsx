import MainLayout from "@/components/layout/main-layout"

export default function QuadLayout({
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
