'use client';

import MainLayout from '@/components/layout/main-layout';
import TAConfigPage from '@/components/ta/TAConfigPage';

export default function TAAggregatorPage() {
    return (
        <MainLayout>
            <div className="container mx-auto p-6">
                <TAConfigPage />
            </div>
        </MainLayout>
    );
}
