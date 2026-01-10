import { captureError, addBreadcrumb } from './sentry';

type AlertHandler = (alert: any) => void;

interface ConnectionHealth {
    status: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' | 'ERROR';
    lastConnected?: Date;
    reconnectAttempts: number;
    messageCount: number;
}

export class AlertWebSocket {
    private ws: WebSocket | null = null;
    private userId: string;
    private url: string;
    private listeners: AlertHandler[] = [];
    private reconnectInterval = 3000; // Initial reconnect delay
    private maxReconnectInterval = 30000; // Max 30 seconds
    private reconnectAttempts = 0;
    private isConnecting = false;
    private messageQueue: any[] = [];
    private throttleInterval = 500; // Throttle to max 2 messages/second
    private lastMessageTime = 0;
    private health: ConnectionHealth = {
        status: 'DISCONNECTED',
        reconnectAttempts: 0,
        messageCount: 0,
    };

    constructor(userId: string = "user123") { // Default user for now
        this.userId = userId;
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const wsUrl = apiUrl.replace(/^http/, 'ws');
        this.url = `${wsUrl}/ws/alerts`;
    }

    /**
     * Get current connection health
     */
    getHealth(): ConnectionHealth {
        return { ...this.health };
    }

    /**
     * Calculate exponential backoff delay
     */
    private getReconnectDelay(): number {
        const delay = Math.min(
            this.reconnectInterval * Math.pow(2, this.reconnectAttempts),
            this.maxReconnectInterval
        );
        // Add jitter (0-20%)
        const jitter = delay * 0.2 * Math.random();
        return delay + jitter;
    }

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return;

        this.isConnecting = true;
        this.health.status = 'CONNECTING';
        console.log(`[AlertWS] Connecting (attempt ${this.reconnectAttempts + 1}): ${this.url}`);

        addBreadcrumb(`WebSocket connecting (attempt ${this.reconnectAttempts + 1})`, 'websocket');

        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[AlertWS] Connected successfully');
                this.isConnecting = false;
                this.reconnectAttempts = 0; // Reset on successful connection
                this.health.status = 'CONNECTED';
                this.health.lastConnected = new Date();
                this.health.reconnectAttempts = 0;
                this.subscribe();

                addBreadcrumb('WebSocket connected', 'websocket');
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    if (message.type === 'alert') {
                        this.health.messageCount++;
                        this.queueMessage(message.data);
                    }
                } catch (e) {
                    console.error('[AlertWS] Error parsing message', e);
                    captureError(e as Error, {
                        tags: { type: 'websocket-parse-error' },
                        extra: { rawMessage: event.data },
                    });
                }
            };

            this.ws.onclose = (event) => {
                console.log(`[AlertWS] Disconnected (code: ${event.code}, reason: ${event.reason})`);
                this.isConnecting = false;
                this.health.status = 'DISCONNECTED';

                addBreadcrumb(`WebSocket disconnected (code: ${event.code})`, 'websocket');

                // Schedule reconnection with exponential backoff
                const delay = this.getReconnectDelay();
                this.reconnectAttempts++;
                this.health.reconnectAttempts = this.reconnectAttempts;

                console.log(`[AlertWS] Reconnecting in ${Math.round(delay)}ms...`);
                setTimeout(() => this.connect(), delay);
            };

            this.ws.onerror = (error) => {
                console.error('[AlertWS] Error:', error);
                this.health.status = 'ERROR';

                captureError(new Error('WebSocket connection error'), {
                    tags: { type: 'websocket-error' },
                    extra: {
                        url: this.url,
                        reconnectAttempts: this.reconnectAttempts,
                    },
                });

                this.ws?.close();
            };
        } catch (error) {
            console.error('[AlertWS] Failed to create WebSocket:', error);
            this.isConnecting = false;
            this.health.status = 'ERROR';

            captureError(error as Error, {
                tags: { type: 'websocket-creation-error' },
            });

            // Retry connection
            const delay = this.getReconnectDelay();
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), delay);
        }
    }

    private subscribe() {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                user_id: this.userId
            }));
        }
    }

    /**
     * Queue message for throttled delivery
     */
    private queueMessage(alert: any) {
        this.messageQueue.push(alert);
        this.processQueue();
    }

    /**
     * Process message queue with throttling
     */
    private processQueue() {
        const now = Date.now();

        if (now - this.lastMessageTime >= this.throttleInterval && this.messageQueue.length > 0) {
            // Batch process multiple messages if queued
            const batch = this.messageQueue.splice(0, 5); // Process up to 5 at once
            batch.forEach(alert => this.notifyListeners(alert));
            this.lastMessageTime = now;
        }

        // Schedule next batch if queue not empty
        if (this.messageQueue.length > 0) {
            setTimeout(() => this.processQueue(), this.throttleInterval);
        }
    }

    addListener(handler: AlertHandler) {
        this.listeners.push(handler);
    }

    removeListener(handler: AlertHandler) {
        this.listeners = this.listeners.filter(h => h !== handler);
    }

    private notifyListeners(alert: any) {
        this.listeners.forEach(handler => {
            try {
                handler(alert);
            } catch (error) {
                console.error('[AlertWS] Error in listener:', error);
                captureError(error as Error, {
                    tags: { type: 'websocket-listener-error' },
                });
            }
        });
    }

    /**
     * Manually disconnect
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.health.status = 'DISCONNECTED';
    }
}

export const alertWS = new AlertWebSocket();
