type AlertHandler = (alert: any) => void;

export class AlertWebSocket {
    private ws: WebSocket | null = null;
    private userId: string;
    private url: string;
    private listeners: AlertHandler[] = [];
    private reconnectInterval = 3000;
    private isConnecting = false;

    constructor(userId: string = "user123") { // Default user for now
        this.userId = userId;
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const wsUrl = apiUrl.replace(/^http/, 'ws');
        this.url = `${wsUrl}/ws/alerts`;
    }

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) return;

        this.isConnecting = true;
        console.log(`Connecting to Alert WebSocket: ${this.url}`);

        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Alert WebSocket Configured');
            this.isConnecting = false;
            this.subscribe();
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'alert') {
                    this.notifyListeners(message.data);
                }
            } catch (e) {
                console.error('Error parsing alert message', e);
            }
        };

        this.ws.onclose = () => {
            console.log('Alert WebSocket Disconnected. Reconnecting...');
            this.isConnecting = false;
            setTimeout(() => this.connect(), this.reconnectInterval);
        };

        this.ws.onerror = (error) => {
            console.error('Alert WebSocket Error:', error);
            this.ws?.close();
        };
    }

    private subscribe() {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                user_id: this.userId
            }));
        }
    }

    addListener(handler: AlertHandler) {
        this.listeners.push(handler);
    }

    removeListener(handler: AlertHandler) {
        this.listeners = this.listeners.filter(h => h !== handler);
    }

    private notifyListeners(alert: any) {
        this.listeners.forEach(handler => handler(alert));
    }
}

export const alertWS = new AlertWebSocket();
