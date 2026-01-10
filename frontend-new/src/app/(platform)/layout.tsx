import { ErrorBoundary } from '@/components/_shared/error-boundary';
import MainLayout from '@/components/layout/main-layout';

export default function PlatformLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ErrorBoundary>
            <MainLayout>{children}</MainLayout>
        </ErrorBoundary>
    );
}
