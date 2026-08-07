export const NGROK_HOST = "trimester-outnumber-unbolted.ngrok-free.dev";

// 💡 Detect if running inside Native Mobile App vs Laptop Web Browser
const isNativeApp = typeof window !== 'undefined' && !!(window as any).Capacitor?.isNativePlatform();

// Laptop Web uses local backend directly; Mobile App uses Ngrok tunnel
export const WS_URL = isNativeApp 
  ? `wss://${NGROK_HOST}/ws` 
  : `ws://localhost:8000/ws`;

type MessageListener = (data: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private listeners: MessageListener[] = [];
  private reconnectInterval: number = 3000;

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    console.log("Connecting WebSocket to:", WS_URL);
    this.socket = new WebSocket(WS_URL);

    this.socket.onopen = () => {
      console.log("⚡ WebSocket Connected Successfully on:", WS_URL);
    };

    this.socket.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        this.listeners.forEach((listener) => listener(parsedData));
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };

    this.socket.onclose = () => {
      console.log("WebSocket Disconnected. Retrying in 3s...");
      this.socket = null;
      setTimeout(() => this.connect(), this.reconnectInterval);
    };
  }

  send(data: object) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket not ready. Reconnecting & retrying...");
      this.connect();
      setTimeout(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify(data));
        }
      }, 500);
    }
  }

  subscribe(callback: MessageListener) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }
}

export const wsService = new WebSocketService();