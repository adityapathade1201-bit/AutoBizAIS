/** Runtime endpoint configuration shared by HTTP and WebSocket clients.
 *
 * Set VITE_API_BASE to the publicly reachable FastAPI URL ending in /api
 * when building the Android app (for example https://your-service.onrender.com/api).
 */
function isNativeApp(): boolean {
    if (typeof window === 'undefined') return false;
    const capacitor = (window as unknown as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
    return capacitor?.isNativePlatform?.() ?? false;
}

export function getApiBase(): string {
    const configured = import.meta.env.VITE_API_BASE?.trim();
    if (configured) {
        const normalized = configured.replace(/\/+$/, '');
        return normalized.endsWith('/api') ? normalized : `${normalized}/api`;
    }

    if (isNativeApp()) {
        throw new Error(
            'Mobile backend URL is not configured. Set VITE_API_BASE to your deployed FastAPI URL (ending in /api), then rebuild and sync the Android app.'
        );
    }

    if (typeof window !== 'undefined' &&
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        return 'http://localhost:8000/api';
    }

    // Production web hosting should proxy /api to the FastAPI service, or set VITE_API_BASE.
    return `${window.location.origin}/api`;
}

export function apiUrl(path: string): string {
    return `${getApiBase()}${path.startsWith('/') ? path : `/${path}`}`;
}

export function getWebSocketUrl(): string {
    const apiBase = getApiBase();
    const serverBase = apiBase.replace(/\/api\/?$/, '');
    const wsBase = serverBase.replace(/^https:/i, 'wss:').replace(/^http:/i, 'ws:');
    return `${wsBase}/ws`;
}
