import { useEffect, useState, useCallback } from 'react';
import { wsManager, WebSocketChannel, WebSocketMessage, MarketTickMessage } from './manager';

/**
 * Hook to subscribe to market data for a specific symbol
 */
export function useMarketData(symbol: string) {
    const [data, setData] = useState<MarketTickMessage | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const handleMessage = (message: WebSocketMessage) => {
            if (message.type === 'tick') {
                setData(message);
            }
        };

        // Subscribe to market data
        wsManager.subscribeToMarket(symbol, handleMessage);

        // Check connection status
        const checkStatus = () => {
            setIsConnected(wsManager.getStatus('market') === 'connected');
        };
        checkStatus();
        const interval = setInterval(checkStatus, 1000);

        // Cleanup
        return () => {
            wsManager.unsubscribeFromMarket(symbol, handleMessage);
            clearInterval(interval);
        };
    }, [symbol]);

    return { data, isConnected };
}

/**
 * Hook to subscribe to alerts
 */
export function useAlerts() {
    const [alerts, setAlerts] = useState<WebSocketMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const handleMessage = (message: WebSocketMessage) => {
            if (message.type === 'alert') {
                setAlerts(prev => [...prev, message]);
            }
        };

        wsManager.subscribeToAlerts(handleMessage);

        const checkStatus = () => {
            setIsConnected(wsManager.getStatus('alerts') === 'connected');
        };
        checkStatus();
        const interval = setInterval(checkStatus, 1000);

        return () => {
            wsManager.unsubscribeFromAlerts(handleMessage);
            clearInterval(interval);
        };
    }, []);

    const clearAlerts = useCallback(() => {
        setAlerts([]);
    }, []);

    return { alerts, isConnected, clearAlerts };
}

/**
 * Hook to subscribe to order updates
 */
export function useOrderUpdates() {
    const [orders, setOrders] = useState<WebSocketMessage[]>([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const handleMessage = (message: WebSocketMessage) => {
            if (message.type === 'order_update') {
                setOrders(prev => [...prev, message]);
            }
        };

        wsManager.subscribeToOrders(handleMessage);

        const checkStatus = () => {
            setIsConnected(wsManager.getStatus('orders') === 'connected');
        };
        checkStatus();
        const interval = setInterval(checkStatus, 1000);

        return () => {
            wsManager.unsubscribeFromOrders(handleMessage);
            clearInterval(interval);
        };
    }, []);

    return { orders, isConnected };
}

/**
 * Hook to get WebSocket connection status
 */
export function useWebSocketStatus(channel: WebSocketChannel) {
    const [status, setStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');

    useEffect(() => {
        const checkStatus = () => {
            setStatus(wsManager.getStatus(channel));
        };

        checkStatus();
        const interval = setInterval(checkStatus, 1000);

        return () => clearInterval(interval);
    }, [channel]);

    return status;
}
