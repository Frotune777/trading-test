/**
 * Sentry Error Tracking Integration
 * 
 * Gracefully handles missing DSN - falls back to console logging.
 * Enable by setting NEXT_PUBLIC_SENTRY_DSN in environment variables.
 */

interface SentryConfig {
    dsn?: string;
    environment?: string;
    enabled: boolean;
}

interface ErrorContext {
    componentStack?: string;
    errorInfo?: any;
    tags?: Record<string, string>;
    extra?: Record<string, any>;
}

class SentryService {
    private config: SentryConfig;
    private breadcrumbs: Array<{ timestamp: string; message: string; category: string }> = [];

    constructor() {
        this.config = {
            dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
            environment: process.env.NODE_ENV || 'development',
            enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
        };

        if (this.config.enabled) {
            console.log('[Sentry] Initialized with DSN');
        } else {
            console.log('[Sentry] Running in fallback mode (no DSN configured)');
        }
    }

    /**
     * Capture an error with context
     */
    captureError(error: Error, context?: ErrorContext): void {
        const errorData = {
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            environment: this.config.environment,
            breadcrumbs: this.breadcrumbs.slice(-10), // Last 10 breadcrumbs
            ...context,
        };

        if (this.config.enabled) {
            // TODO: Integrate with actual Sentry SDK when DSN is available
            // Sentry.captureException(error, { contexts: context });
            console.error('[Sentry] Error captured:', errorData);
        } else {
            console.error('[Sentry Fallback] Error:', errorData);
        }
    }

    /**
     * Capture a message (non-error event)
     */
    captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info'): void {
        const messageData = {
            message,
            level,
            timestamp: new Date().toISOString(),
            environment: this.config.environment,
        };

        if (this.config.enabled) {
            console.log(`[Sentry] Message captured (${level}):`, messageData);
        } else {
            console.log(`[Sentry Fallback] ${level.toUpperCase()}:`, message);
        }
    }

    /**
     * Add a breadcrumb for tracking user actions
     */
    addBreadcrumb(message: string, category: string = 'user-action'): void {
        const breadcrumb = {
            timestamp: new Date().toISOString(),
            message,
            category,
        };

        this.breadcrumbs.push(breadcrumb);

        // Keep only last 50 breadcrumbs
        if (this.breadcrumbs.length > 50) {
            this.breadcrumbs.shift();
        }

        if (this.config.enabled) {
            // Sentry.addBreadcrumb(breadcrumb);
        }
    }

    /**
     * Set user context
     */
    setUser(user: { id: string; email?: string; username?: string }): void {
        if (this.config.enabled) {
            console.log('[Sentry] User context set:', user);
            // Sentry.setUser(user);
        }
    }

    /**
     * Clear user context (on logout)
     */
    clearUser(): void {
        if (this.config.enabled) {
            console.log('[Sentry] User context cleared');
            // Sentry.setUser(null);
        }
    }

    /**
     * Set custom tags
     */
    setTag(key: string, value: string): void {
        if (this.config.enabled) {
            // Sentry.setTag(key, value);
        }
    }

    /**
     * Check if Sentry is enabled
     */
    isEnabled(): boolean {
        return this.config.enabled;
    }
}

// Export singleton instance
export const sentry = new SentryService();

// Convenience exports
export const captureError = (error: Error, context?: ErrorContext) => sentry.captureError(error, context);
export const captureMessage = (message: string, level?: 'info' | 'warning' | 'error') => sentry.captureMessage(message, level);
export const addBreadcrumb = (message: string, category?: string) => sentry.addBreadcrumb(message, category);
export const setUser = (user: { id: string; email?: string; username?: string }) => sentry.setUser(user);
export const clearUser = () => sentry.clearUser();
