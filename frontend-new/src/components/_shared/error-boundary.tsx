'use client';

import { Component, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: any) => void;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: any) {
        console.error('ErrorBoundary caught:', error, errorInfo);
        this.props.onError?.(error, errorInfo);

        // TODO: Send to monitoring service
        // sendToSentry(error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex flex-col items-center justify-center p-8 space-y-4">
                    <AlertTriangle className="w-12 h-12 text-destructive" />
                    <h2 className="text-xl font-semibold">Something went wrong</h2>
                    <p className="text-muted-foreground text-center max-w-md">
                        {this.state.error?.message || 'An unexpected error occurred'}
                    </p>
                    <Button onClick={() => this.setState({ hasError: false })}>
                        Try Again
                    </Button>
                </div>
            );
        }

        return this.props.children;
    }
}
