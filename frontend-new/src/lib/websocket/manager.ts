import ReconnectingWebSocket from 'reconnecting-websocket';

export type WebSocketChannel = 'market' | 'alerts' | 'orders';

export interface MarketTickMessage {
    type: 'tick';
    symbol: string;
    ltp: number;
    volume: number;
    timestamp: string;
}

export interface AlertMessage {
    type: 'alert';
    severity: 'critical' | 'warning' | 'info';
    message: string;
    timestamp: string;
}

export interface OrderUpdateMessage {
    type: 'order_update';
    order_id: string;
    status: string;
    symbol: string;
    timestamp: string;
}

export type WebSocketMessage = MarketTickMessage | AlertMessage | OrderUpdateMessage;

type MessageCallback = (message: WebSocketMessage) => void;

class WebSocketManager {
    private connections: Map<WebSocketChannel, ReconnectingWebSocket> = new Map();
    private subscribers: Map<WebSocketChannel, Map<string, Set<MessageCallback>>> = new Map();
    private connectionStatus: Map<WebSocketChannel, 'connected' | 'connecting' | 'disconnected'> = new Map();

    constructor() {
        // Initialize subscriber maps for each channel
        this.subscribers.set('market', new Map());
        this.subscribers.set('alerts', new Map());
        this.subscribers.set('orders', new Map());

        // Initialize connection status
        this.connectionStatus.set('market', 'disconnected');
        this.connectionStatus.set('alerts', 'disconnected');
        this.connectionStatus.set('orders', 'disconnected');
    }

    /**
     * Connect to a WebSocket channel
     */
    connect(channel: WebSocketChannel) {
        if (this.connections.has(channel)) {
            return; // Already connected
        }

        // Backend has a single WebSocket endpoint at /api/v1/ws
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
        const url = `${wsUrl}/api/v1/ws`;

        this.connectionStatus.set(channel, 'connecting');

        const ws = new ReconnectingWebSocket(url, [], {
            maxRetries: 10,
            reconnectionDelayGrowFactor: 1.3,
            maxReconnectionDelay: 10000,
            minReconnectionDelay: 1000,
        });

        ws.addEventListener('open', () => {
            console.log(`[WebSocket] Connected to ${channel}`);
            this.connectionStatus.set(channel, 'connected');
        });

        ws.addEventListener('close', () => {
            console.log(`[WebSocket] Disconnected from ${channel}`);
            this.connectionStatus.set(channel, 'disconnected');
        });

        ws.addEventListener('error', (error) => {
            console.error(`[WebSocket] Error on ${channel}:`, error);
        });

        ws.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data) as WebSocketMessage;
                this.handleMessage(channel, data);
            } catch (error) {
                console.error(`[WebSocket] Failed to parse message on ${channel}:`, error);
            }
        });

        this.connections.set(channel, ws);
    }

    /**
     * Disconnect from a WebSocket channel
     */
    disconnect(channel: WebSocketChannel) {
        const ws = this.connections.get(channel);
        if (ws) {
            ws.close();
            this.connections.delete(channel);
            this.connectionStatus.set(channel, 'disconnected');
        }
    }

    /**
     * Subscribe to market data for a specific symbol
     */
    subscribeToMarket(symbol: string, callback: MessageCallback) {
        this.subscribe('market', symbol, callback);

        // Send subscription message to server
        const ws = this.connections.get('market');
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: 'subscribe',
                symbols: [symbol],
            }));
        }
    }

    /**
     * Unsubscribe from market data for a specific symbol
     */
    unsubscribeFromMarket(symbol: string, callback: MessageCallback) {
        this.unsubscribe('market', symbol, callback);

        // Send unsubscribe message to server
        const subscribers = this.subscribers.get('market')?.get(symbol);
        if (!subscribers || subscribers.size === 0) {
            const ws = this.connections.get('market');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    action: 'unsubscribe',
                    symbols: [symbol],
                }));
            }
        }
    }

    /**
     * Subscribe to alerts
     */
    subscribeToAlerts(callback: MessageCallback) {
        this.subscribe('alerts', 'all', callback);
    }

    /**
     * Unsubscribe from alerts
     */
    unsubscribeFromAlerts(callback: MessageCallback) {
        this.unsubscribe('alerts', 'all', callback);
    }

    /**
     * Subscribe to order updates
     */
    subscribeToOrders(callback: MessageCallback) {
        this.subscribe('orders', 'all', callback);
    }

    /**
     * Unsubscribe from order updates
     */
    unsubscribeFromOrders(callback: MessageCallback) {
        this.unsubscribe('orders', 'all', callback);
    }

    /**
     * Get connection status for a channel
     */
    getStatus(channel: WebSocketChannel): 'connected' | 'connecting' | 'disconnected' {
        return this.connectionStatus.get(channel) || 'disconnected';
    }

    /**
     * Internal: Subscribe to a channel with a key
     */
    private subscribe(channel: WebSocketChannel, key: string, callback: MessageCallback) {
        // Ensure connection exists
        if (!this.connections.has(channel)) {
            this.connect(channel);
        }

        // Get or create subscriber set for this key
        const channelSubscribers = this.subscribers.get(channel)!;
        if (!channelSubscribers.has(key)) {
            channelSubscribers.set(key, new Set());
        }
        channelSubscribers.get(key)!.add(callback);
    }

    /**
     * Internal: Unsubscribe from a channel with a key
     */
    private unsubscribe(channel: WebSocketChannel, key: string, callback: MessageCallback) {
        const channelSubscribers = this.subscribers.get(channel);
        if (!channelSubscribers) return;

        const keySubscribers = channelSubscribers.get(key);
        if (!keySubscribers) return;

        keySubscribers.delete(callback);

        // Clean up empty subscriber sets
        if (keySubscribers.size === 0) {
            channelSubscribers.delete(key);
        }

        // Disconnect if no more subscribers
        if (channelSubscribers.size === 0) {
            this.disconnect(channel);
        }
    }

    /**
     * Internal: Handle incoming messages
     */
    private handleMessage(channel: WebSocketChannel, message: WebSocketMessage) {
        const channelSubscribers = this.subscribers.get(channel);
        if (!channelSubscribers) return;

        // For market data, route by symbol
        if (channel === 'market' && message.type === 'tick') {
            const subscribers = channelSubscribers.get(message.symbol);
            if (subscribers) {
                subscribers.forEach(callback => callback(message));
            }
        }
        // For alerts and orders, route to 'all' subscribers
        else {
            const subscribers = channelSubscribers.get('all');
            if (subscribers) {
                subscribers.forEach(callback => callback(message));
            }
        }
    }
}

// Singleton instance
export const wsManager = new WebSocketManager();
