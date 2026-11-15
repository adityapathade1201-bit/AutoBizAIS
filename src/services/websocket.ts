import { getWebSocketUrl } from './config';

type MessageListener = (data: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private listeners: MessageListener[] = [];
  private readonly reconnectInterval = 3000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingMessages: string[] = [];

  connect() {
    if (typeof window === 'undefined' || typeof WebSocket === 'undefined') return;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    let wsUrl: string;
    try {
      wsUrl = getWebSocketUrl();
    } catch (error) {
      console.error('AutoBiz AI WebSocket is not configured:', error);
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    console.log('Connecting WebSocket to:', wsUrl);
    try {
      this.socket = new WebSocket(wsUrl);
    } catch (error) {
      console.error('Unable to create AutoBiz AI WebSocket:', error);
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      console.log('AutoBiz AI WebSocket connected:', wsUrl);
      // Deliver events queued while the connection was offline.
      while (this.pendingMessages.length > 0 && this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(this.pendingMessages.shift()!);
      }
    };

    this.socket.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        this.listeners.forEach((listener) => listener(parsedData));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('AutoBiz AI WebSocket error:', error);
    };

    this.socket.onclose = () => {
      console.warn('AutoBiz AI WebSocket disconnected. Retrying in 3 seconds...');
      this.socket = null;
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectInterval);
  }

  send(data: object) {
    const serialized = JSON.stringify(data);
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(serialized);
      return;
    }

    this.pendingMessages.push(serialized);
    console.warn('WebSocket is not connected. Message queued until reconnection.');
    this.connect();
  }

  subscribe(callback: MessageListener) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((listener) => listener !== callback);
    };
  }
}

export const wsService = new WebSocketService();
