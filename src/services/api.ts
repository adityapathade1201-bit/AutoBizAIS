/**
 * API Service Layer for AutoBiz AI
 */

import type { Agent, Conversation, BusinessMetrics, ChartPoint, Recommendation, MarketplaceAgent, OnboardingConfig, OnboardingData } from '../types';
import { apiUrl } from './config';

// Public endpoints are configured through VITE_API_BASE; no temporary tunnel is hardcoded.
const USE_MOCK = false;

/**
 * Smart Fetch: Tries Backend API first.
 * If a read endpoint is unavailable, it can load the bundled static JSON.
 */
async function fetchJSON<T>(path: string, fallbackJsonPath?: string): Promise<T> {
    try {
        const isApiCall = path.startsWith('http');
        const headers: Record<string, string> = {};

        if (isApiCall) {
            headers['ngrok-skip-browser-warning'] = 'true';
        }

        const res = await fetch(path, { headers });
        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
        return await res.json();
    } catch (error) {
        if (fallbackJsonPath) {
            console.warn(`Backend endpoint ${path} not ready. Loading local fallback: ${fallbackJsonPath}`);
            const fallbackRes = await fetch(fallbackJsonPath);
            if (fallbackRes.ok) return await fallbackRes.json();
        }
        throw error;
    }
}

export const api = {
    // ──────────────────────── Agents ────────────────────────

    /** Get all hired agents */
    getAgents: async (): Promise<Agent[]> => {
        if (USE_MOCK) {
            const data = await fetchJSON<{ agents: Agent[] }>('/data/agents.json');
            return data.agents;
        }
        try {
            const data = await fetchJSON<{ agents: Agent[] }>(apiUrl('/agents'), '/data/agents.json');
            return data.agents || data;
        } catch {
            const data = await fetchJSON<{ agents: Agent[] }>('/data/agents.json');
            return data.agents;
        }
    },

    /** Get chat history for a specific agent */
    getChatHistory: async (agentId: string): Promise<Conversation | null> => {
        if (USE_MOCK) {
            const data = await fetchJSON<{ conversations: Record<string, Conversation> }>('/data/chat-history.json');
            return data.conversations[agentId] || null;
        }
        try {
            const data = await fetchJSON<{ conversations: Record<string, Conversation> }>(apiUrl(`/chat/${encodeURIComponent(agentId)}`), '/data/chat-history.json');
            return data.conversations ? (data.conversations[agentId] || null) : (data as any);
        } catch {
            const data = await fetchJSON<{ conversations: Record<string, Conversation> }>('/data/chat-history.json');
            return data.conversations[agentId] || null;
        }
    },

    /** Send a message to an agent — returns the agent's reply */
    sendMessage: async (agentId: string, message: string): Promise<{ reply: string; toolExecution?: { tool: string; content: string } }> => {
        // Never fake an AI response when the backend is unavailable. Surface the real failure.
        const endpoint = apiUrl('/chat');
        let res: Response;
        try {
            res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId, message }),
            });
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error(`Cannot reach the AutoBiz AI backend at ${endpoint}. Check the backend deployment, internet connection, and CORS configuration.`);
            }
            throw error;
        }

        const responseText = await res.text();
        let payload: { reply?: unknown; detail?: unknown; message?: unknown } = {};
        try {
            payload = responseText ? JSON.parse(responseText) as typeof payload : {};
        } catch {
            // Keep the HTTP status as the useful diagnostic for non-JSON proxy responses.
        }

        if (!res.ok) {
            const detail = typeof payload.detail === 'string'
                ? payload.detail
                : typeof payload.message === 'string' ? payload.message : responseText;
            throw new Error(`Backend returned HTTP ${res.status}${detail ? `: ${detail}` : ''}`);
        }

        if (typeof payload.reply !== 'string' || !payload.reply.trim()) {
            throw new Error('The backend responded without an AI reply. Check the backend logs and OpenRouter configuration.');
        }

        return payload as { reply: string; toolExecution?: { tool: string; content: string } };
    },

    // ──────────────────────── Business ────────────────────────

    /** Get business metrics */
    getMetrics: async (): Promise<BusinessMetrics> => {
        try {
            const data = await fetchJSON<{ metrics: BusinessMetrics }>(apiUrl('/business/metrics'), '/data/business-metrics.json');
            return data.metrics || data;
        } catch {
            const data = await fetchJSON<{ metrics: BusinessMetrics }>('/data/business-metrics.json');
            return data.metrics;
        }
    },

    /** Get chart data */
    getChartData: async (): Promise<Record<string, ChartPoint[]>> => {
        try {
            const data = await fetchJSON<{ chartData: Record<string, ChartPoint[]> }>(apiUrl('/business/charts'), '/data/business-metrics.json');
            return data.chartData || data;
        } catch {
            const data = await fetchJSON<{ chartData: Record<string, ChartPoint[]> }>('/data/business-metrics.json');
            return data.chartData;
        }
    },

    /** Get AI recommendations */
    getRecommendations: async (): Promise<Recommendation[]> => {
        try {
            const data = await fetchJSON<{ ai_recommendations: Recommendation[] }>(apiUrl('/business/recommendations'), '/data/business-metrics.json');
            return data.ai_recommendations || data;
        } catch {
            const data = await fetchJSON<{ ai_recommendations: Recommendation[] }>('/data/business-metrics.json');
            return data.ai_recommendations;
        }
    },

    // ──────────────────────── Marketplace ────────────────────────

    /** Get marketplace agents */
    getMarketplaceAgents: async (): Promise<MarketplaceAgent[]> => {
        try {
            const data = await fetchJSON<{ featured_agents: MarketplaceAgent[] }>(apiUrl('/marketplace'), '/data/marketplace-agents.json');
            return data.featured_agents || data;
        } catch {
            const data = await fetchJSON<{ featured_agents: MarketplaceAgent[] }>('/data/marketplace-agents.json');
            return data.featured_agents;
        }
    },

    /** Get marketplace categories */
    getCategories: async (): Promise<string[]> => {
        try {
            const data = await fetchJSON<{ categories: string[] }>(apiUrl('/marketplace/categories'), '/data/marketplace-agents.json');
            return data.categories || data;
        } catch {
            const data = await fetchJSON<{ categories: string[] }>('/data/marketplace-agents.json');
            return data.categories;
        }
    },

    // ──────────────────────── Onboarding ────────────────────────

    /** Get onboarding config */
    getOnboardingConfig: async (): Promise<OnboardingConfig> => {
        return fetchJSON('/data/onboarding-config.json');
    },

    /** Analyze business data */
    analyzeBusiness: async (_data: OnboardingData): Promise<{ summary: string; recommended_agents: Array<{ agent_id: string; reason: string }> }> => {
        try {
            const res = await fetch(apiUrl('/onboarding/analyze'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(_data),
            });
            if (!res.ok) throw new Error("API failed");
            return await res.json();
        } catch {
            const config = await fetchJSON<OnboardingConfig>('/data/onboarding-config.json');
            return config.mock_response;
        }
    },

    /** Upload documents */
    uploadDocuments: async (_files: File[]): Promise<{ success: boolean; fileIds: string[] }> => {
        try {
            const formData = new FormData();
            _files.forEach(f => formData.append('files', f));
            const res = await fetch(apiUrl('/upload'), {
                method: 'POST',
                headers: { 'ngrok-skip-browser-warning': 'true' },
                body: formData
            });
            if (!res.ok) throw new Error("API failed");
            return await res.json();
        } catch {
            return { success: true, fileIds: _files.map((_, i) => `file-${i}`) };
        }
    },

    // ──────────────────────── Agent Management ────────────────────────

    /** Create a new custom agent */
    createAgent: async (config: Partial<Agent>): Promise<Agent> => {
        try {
            const res = await fetch(apiUrl('/agents/create'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(config),
            });
            if (!res.ok) throw new Error("API failed");
            return await res.json();
        } catch {
            return { id: `custom-${Date.now()}`, status: 'online', avatar: '🤖', color: '#6366f1', ...config } as Agent;
        }
    },

    /** Update agent settings */
    updateAgentSettings: async (id: string, settings: Partial<Agent>): Promise<Agent> => {
        try {
            const res = await fetch(apiUrl(`/agents/${encodeURIComponent(id)}`), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(settings),
            });
            if (!res.ok) throw new Error("API failed");
            return await res.json();
        } catch {
            return { id, ...settings } as Agent;
        }
    },
};
