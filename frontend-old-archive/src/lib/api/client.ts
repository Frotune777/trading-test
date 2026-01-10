import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { captureError, addBreadcrumb } from '../sentry';

// Circuit breaker state
interface CircuitBreakerState {
    failures: number;
    lastFailureTime: number;
    state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
}

const circuitBreakers = new Map<string, CircuitBreakerState>();
const CIRCUIT_BREAKER_THRESHOLD = 5; // Open circuit after 5 failures
const CIRCUIT_BREAKER_TIMEOUT = 30000; // Try again after 30 seconds

/**
 * Get or create circuit breaker for an endpoint
 */
function getCircuitBreaker(endpoint: string): CircuitBreakerState {
    if (!circuitBreakers.has(endpoint)) {
        circuitBreakers.set(endpoint, {
            failures: 0,
            lastFailureTime: 0,
            state: 'CLOSED',
        });
    }
    return circuitBreakers.get(endpoint)!;
}

/**
 * Check if circuit breaker allows request
 */
function canMakeRequest(endpoint: string): boolean {
    const breaker = getCircuitBreaker(endpoint);
    const now = Date.now();

    if (breaker.state === 'CLOSED') {
        return true;
    }

    if (breaker.state === 'OPEN') {
        // Check if timeout has passed
        if (now - breaker.lastFailureTime > CIRCUIT_BREAKER_TIMEOUT) {
            breaker.state = 'HALF_OPEN';
            return true;
        }
        return false;
    }

    // HALF_OPEN state - allow one request
    return true;
}

/**
 * Record request success
 */
function recordSuccess(endpoint: string): void {
    const breaker = getCircuitBreaker(endpoint);
    breaker.failures = 0;
    breaker.state = 'CLOSED';
}

/**
 * Record request failure
 */
function recordFailure(endpoint: string): void {
    const breaker = getCircuitBreaker(endpoint);
    breaker.failures++;
    breaker.lastFailureTime = Date.now();

    if (breaker.failures >= CIRCUIT_BREAKER_THRESHOLD) {
        breaker.state = 'OPEN';
        console.warn(`[Circuit Breaker] Opened for endpoint: ${endpoint}`);
    }
}

/**
 * Exponential backoff with jitter
 */
function getRetryDelay(retryCount: number): number {
    const baseDelay = 1000; // 1 second
    const maxDelay = 10000; // 10 seconds
    const exponentialDelay = Math.min(baseDelay * Math.pow(2, retryCount), maxDelay);
    const jitter = Math.random() * 0.3 * exponentialDelay; // 0-30% jitter
    return exponentialDelay + jitter;
}

/**
 * Retry logic with exponential backoff
 */
async function retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    endpoint: string,
    maxRetries: number = 3
): Promise<AxiosResponse<T>> {
    let lastError: AxiosError | undefined;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            // Check circuit breaker
            if (!canMakeRequest(endpoint)) {
                throw new Error(`Circuit breaker is OPEN for ${endpoint}`);
            }

            const response = await requestFn();
            recordSuccess(endpoint);
            return response;
        } catch (error) {
            lastError = error as AxiosError;
            recordFailure(endpoint);

            // Don't retry on client errors (4xx) except 429 (rate limit)
            if (lastError.response?.status && lastError.response.status >= 400 && lastError.response.status < 500) {
                if (lastError.response.status !== 429) {
                    throw lastError;
                }
            }

            // Don't retry on last attempt
            if (attempt === maxRetries) {
                break;
            }

            const delay = getRetryDelay(attempt);
            console.log(`[API Retry] Attempt ${attempt + 1}/${maxRetries} failed. Retrying in ${Math.round(delay)}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw lastError;
}

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add breadcrumb for tracking
        addBreadcrumb(`API Request: ${config.method?.toUpperCase()} ${config.url}`, 'api');

        // Add request timestamp
        (config as any).metadata = { startTime: Date.now() };

        return config;
    },
    (error) => {
        captureError(error, {
            tags: { type: 'api-request-error' },
        });
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        // Calculate request duration
        const duration = Date.now() - (response.config as any).metadata?.startTime;

        if (duration > 5000) {
            console.warn(`[API] Slow request: ${response.config.url} took ${duration}ms`);
        }

        return response;
    },
    (error: AxiosError) => {
        const duration = Date.now() - (error.config as any)?.metadata?.startTime;

        // Log error to Sentry
        captureError(error as Error, {
            tags: {
                type: 'api-response-error',
                status: error.response?.status?.toString() || 'unknown',
                endpoint: error.config?.url || 'unknown',
            },
            extra: {
                method: error.config?.method,
                url: error.config?.url,
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                duration,
            },
        });

        // Add user-friendly error message
        if (error.response?.status === 401) {
            console.error('[API] Unauthorized - redirecting to login');
        } else if (error.response?.status === 403) {
            console.error('[API] Forbidden - insufficient permissions');
        } else if (error.response?.status === 500) {
            console.error('[API] Server error - please try again later');
        } else if (!error.response) {
            console.error('[API] Network error - check your connection');
        }

        return Promise.reject(error);
    }
);

/**
 * Enhanced API methods with retry logic
 */
const apiWithRetry = {
    get: <T = any>(url: string, config?: AxiosRequestConfig) =>
        retryRequest<T>(() => api.get<T>(url, config), url),

    post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
        retryRequest<T>(() => api.post<T>(url, data, config), url),

    put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
        retryRequest<T>(() => api.put<T>(url, data, config), url),

    delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
        retryRequest<T>(() => api.delete<T>(url, config), url),

    patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
        retryRequest<T>(() => api.patch<T>(url, data, config), url),
};

export const StockService = {
    getStocks: () => apiWithRetry.get('/data/stocks'),
    getOHLCV: (symbol: string, timeframe: string) =>
        apiWithRetry.get(`/data/ohlcv/${symbol}`, { params: { timeframe } }),
    getAnalysis: (symbol: string) => apiWithRetry.get(`/analysis/indicators/${symbol}`),
    getPrediction: (symbol: string) => apiWithRetry.get(`/predictions/${symbol}`),
};

export { apiWithRetry as api };
export default apiWithRetry;
