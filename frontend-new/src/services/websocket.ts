/**
 * WebSocket Service for Real-Time Market Data
 * Connects to backend WebSocket server and manages subscriptions
 */

export interface MarketTick {
  type: 'tick';
  symbol: string;
  exchange: string;
  ltp: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  oi?: number;
  timestamp: string;
}

export interface SubscriptionOptions {
  symbols: string[];
  mode: 'ltp' | 'quote' | 'full';
}

type MessageHandler = (data: MarketTick) => void;
type ErrorHandler = (error: Error) => void;
type StatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private apiKey: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private subscriptions: Set<string> = new Set();
  private currentMode: 'ltp' | 'quote' | 'full' = 'ltp';

  constructor(url: string = 'ws://localhost:8765', apiKey: string = '') {
    this.url = url;
    this.apiKey = apiKey;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.updateStatus('connecting');

      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
        this.authenticate()
          .then(() => {
            this.updateStatus('connected');
            resolve();
          })
          .catch(reject);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.updateStatus('error');
        this.notifyError(new Error('WebSocket connection error'));
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.updateStatus('disconnected');
        this.attemptReconnect();
      };
    });
  }

  /**
   * Authenticate with API key
   */
  private authenticate(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const authHandler = (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        if (data.type === 'authenticated') {
          console.log('✅ Authenticated:', data.username);
          this.ws?.removeEventListener('message', authHandler);
          resolve();
        } else if (data.type === 'error') {
          this.ws?.removeEventListener('message', authHandler);
          reject(new Error(data.error));
        }
      };

      this.ws.addEventListener('message', authHandler);

      this.send({
        type: 'auth',
        api_key: this.apiKey,
      });
    });
  }

  /**
   * Subscribe to symbols
   */
  subscribe(options: SubscriptionOptions): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const subHandler = (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        if (data.type === 'subscribed') {
          options.symbols.forEach((symbol) => this.subscriptions.add(symbol));
          this.currentMode = options.mode;
          this.ws?.removeEventListener('message', subHandler);
          resolve();
        } else if (data.type === 'error') {
          this.ws?.removeEventListener('message', subHandler);
          reject(new Error(data.error));
        }
      };

      this.ws.addEventListener('message', subHandler);

      this.send({
        type: 'subscribe',
        symbols: options.symbols,
        mode: options.mode,
      });
    });
  }

  /**
   * Unsubscribe from symbols
   */
  unsubscribe(symbols: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.send({
      type: 'unsubscribe',
      symbols,
    });

    symbols.forEach((symbol) => this.subscriptions.delete(symbol));
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(data: any): void {
    switch (data.type) {
      case 'tick':
        this.messageHandlers.forEach((handler) => handler(data as MarketTick));
        break;
      case 'error':
        this.notifyError(new Error(data.error));
        break;
      case 'authenticated':
      case 'subscribed':
      case 'unsubscribed':
      case 'pong':
        // Handled by promise callbacks
        break;
      default:
        console.warn('Unknown message type:', data.type);
    }
  }

  /**
   * Send message to server
   */
  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      this.notifyError(new Error('Failed to reconnect to WebSocket'));
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    setTimeout(() => {
      this.connect()
        .then(() => {
          // Re-subscribe to previous symbols
          if (this.subscriptions.size > 0) {
            return this.subscribe({
              symbols: Array.from(this.subscriptions),
              mode: this.currentMode,
            });
          }
        })
        .catch((error) => {
          console.error('Reconnect failed:', error);
        });
    }, delay);
  }

  /**
   * Register message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Register error handler
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  /**
   * Register status handler
   */
  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  /**
   * Notify error handlers
   */
  private notifyError(error: Error): void {
    this.errorHandlers.forEach((handler) => handler(error));
  }

  /**
   * Update connection status
   */
  private updateStatus(status: 'connecting' | 'connected' | 'disconnected' | 'error'): void {
    this.statusHandlers.forEach((handler) => handler(status));
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscriptions.clear();
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get subscribed symbols
   */
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }
}

// Singleton instance
let wsInstance: WebSocketService | null = null;

export function getWebSocketService(apiKey?: string): WebSocketService {
  if (!wsInstance) {
    // Get WebSocket URL from environment or use default
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    // Remove any trailing slashes
    const url = wsUrl.replace(/\/$/, '');
    wsInstance = new WebSocketService(url, apiKey || '');
  }
  return wsInstance;
}
