'use client';

import React, { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { captureError } from '@/lib/sentry';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
    errorInfo?: ErrorInfo;
}

class ErrorBoundary extends React.Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);

        // Log to Sentry with component stack
        captureError(error, {
            componentStack: errorInfo.componentStack ?? undefined,
            errorInfo,
            tags: {
                errorBoundary: 'true',
                component: 'ErrorBoundary',
            },
        });

        // Store errorInfo in state for reporting
        this.setState({ errorInfo });
    }

    private handleReportIssue = () => {
        const { error, errorInfo } = this.state;

        // Create issue report with error details
        const issueBody = encodeURIComponent(
            `**Error Message:**\n${error?.message || 'Unknown error'}\n\n` +
            `**Stack Trace:**\n\`\`\`\n${error?.stack || 'No stack trace'}\n\`\`\`\n\n` +
            `**Component Stack:**\n\`\`\`\n${errorInfo?.componentStack || 'No component stack'}\n\`\`\`\n\n` +
            `**Environment:**\n- User Agent: ${navigator.userAgent}\n` +
            `- Timestamp: ${new Date().toISOString()}\n` +
            `- URL: ${window.location.href}`
        );

        // Open GitHub issue (or email, or support form)
        // For now, copy to clipboard
        navigator.clipboard.writeText(decodeURIComponent(issueBody)).then(() => {
            alert('Error details copied to clipboard. Please share with the development team.');
        });
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-[400px] flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-900 rounded-2xl border border-red-100 dark:border-red-900/30 shadow-xl text-center">
                    <div className="w-20 h-20 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6">
                        <AlertTriangle className="w-10 h-10 text-red-600 dark:text-red-400" />
                    </div>

                    <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-2 uppercase tracking-tight">
                        Something went wrong
                    </h2>

                    <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
                        The component encountered an unexpected error. This has been logged and we're looking into it.
                    </p>

                    <div className="flex gap-4">
                        <button
                            onClick={() => this.setState({ hasError: false, error: undefined, errorInfo: undefined })}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold uppercase tracking-widest text-xs hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-500/20"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try Again
                        </button>

                        <button
                            onClick={this.handleReportIssue}
                            className="flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-xl font-bold uppercase tracking-widest text-xs hover:bg-orange-700 transition-all shadow-lg shadow-orange-500/20"
                        >
                            <Bug className="w-4 h-4" />
                            Report Issue
                        </button>

                        <a
                            href="/"
                            className="flex items-center gap-2 px-6 py-3 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-xl font-bold uppercase tracking-widest text-xs hover:bg-gray-200 dark:hover:bg-gray-700 transition-all"
                        >
                            <Home className="w-4 h-4" />
                            Go Home
                        </a>
                    </div>

                    {process.env.NODE_ENV === 'development' && this.state.error && (
                        <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-left overflow-auto max-w-full">
                            <p className="font-mono text-[10px] text-red-600 dark:text-red-400 whitespace-pre-wrap">
                                {this.state.error.stack}
                            </p>
                            {this.state.errorInfo?.componentStack && (
                                <details className="mt-4">
                                    <summary className="cursor-pointer text-xs font-semibold text-gray-700 dark:text-gray-300">
                                        Component Stack
                                    </summary>
                                    <p className="font-mono text-[10px] text-gray-600 dark:text-gray-400 mt-2 whitespace-pre-wrap">
                                        {this.state.errorInfo.componentStack}
                                    </p>
                                </details>
                            )}
                        </div>
                    )}
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
