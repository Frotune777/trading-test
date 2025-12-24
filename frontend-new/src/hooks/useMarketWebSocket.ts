import { useState, useEffect, useCallback, useRef } from 'react';

interface TickData {
    ltp: number;
    ts: number;
    source: string;
}

interface WebSocketMessage {
    type: 'tick' | 'pong';
    symbol?: string;
    data?: TickData;
}

export const useMarketWebSocket = (symbols: string[] = ['ALL']) => {
    const [livePrices, setLivePrices] = useState<Record<string, number>>({});
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef<WebSocket | null>(null);
    const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        // Construct WS URL - handle both local development and production-like scenarios
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
        const wsUrl = `${protocol}//${host}/api/v1/ws`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log('Market WebSocket connected');
            setIsConnected(true);
            // Subscribe to requested symbols
            ws.current?.send(JSON.stringify({
                action: 'subscribe',
                symbols: symbols
            }));
        };

        ws.current.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                if (message.type === 'tick' && message.symbol && message.data) {
                    setLivePrices((prev) => ({
                        ...prev,
                        [message.symbol!]: message.data!.ltp
                    }));
                }
            } catch (error) {
                console.error('Error parsing WS message:', error);
            }
        };

        ws.current.onclose = () => {
            console.log('Market WebSocket disconnected');
            setIsConnected(false);
            // Exponential backoff or simple retry
            reconnectTimeout.current = setTimeout(connect, 5000);
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            ws.current?.close();
        };
    }, [symbols]);

    useEffect(() => {
        connect();
        return () => {
            if (ws.current) {
                ws.current.close();
            }
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
        };
    }, [connect]);

    return { livePrices, isConnected };
};

export default useMarketWebSocket;
