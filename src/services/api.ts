/**
 * API Service Layer for AutoBiz AI
 */

import type { Agent, Conversation, BusinessMetrics, ChartPoint, Recommendation, MarketplaceAgent, OnboardingConfig, OnboardingData } from '../types';

// Set this to false so it tries backend first, and falls back to JSON if backend endpoint missing
const USE_MOCK = false;

const API_BASE = 'https://trimester-outnumber-unbolted.ngrok-free.dev/api';

/**
 * Smart Fetch: Tries Backend API first. 
 * If backend fails or endpoint doesn't exist, automatically loads local bundled JSON!
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
            const data = await fetchJSON<{ agents: Agent[] }>(`${API_BASE}/agents`, '/data/agents.json');
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
            const data = await fetchJSON<{ conversations: Record<string, Conversation> }>(`${API_BASE}/chat/${agentId}`, '/data/chat-history.json');
            return data.conversations ? (data.conversations[agentId] || null) : (data as any);
        } catch {
            const data = await fetchJSON<{ conversations: Record<string, Conversation> }>('/data/chat-history.json');
            return data.conversations[agentId] || null;
        }
    },

    /** Send a message to an agent — returns the agent's reply */
    sendMessage: async (agentId: string, message: string): Promise<{ reply: string; toolExecution?: { tool: string; content: string } }> => {
        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({ agent_id: agentId, message }),
            });
            if (!res.ok) throw new Error("API failed");
            return await res.json();
        } catch {
            // Fallback response if backend chat POST fails
            await new Promise(r => setTimeout(r, 1000));
            return {
                reply: `[AutoBiz AI Agent] I received your message: "${message}". Processed via fallback pipeline.`,
            };
        }
    },

    // ──────────────────────── Business ────────────────────────

    /** Get business metrics */
    getMetrics: async (): Promise<BusinessMetrics> => {
        try {
            const data = await fetchJSON<{ metrics: BusinessMetrics }>(`${API_BASE}/business/metrics`, '/data/business-metrics.json');
            return data.metrics || data;
        } catch {
            const data = await fetchJSON<{ metrics: BusinessMetrics }>('/data/business-metrics.json');
            return data.metrics;
        }
    },

    /** Get chart data */
    getChartData: async (): Promise<Record<string, ChartPoint[]>> => {
        try {
            const data = await fetchJSON<{ chartData: Record<string, ChartPoint[]> }>(`${API_BASE}/business/charts`, '/data/business-metrics.json');
            return data.chartData || data;
        } catch {
            const data = await fetchJSON<{ chartData: Record<string, ChartPoint[]> }>('/data/business-metrics.json');
            return data.chartData;
        }
    },

    /** Get AI recommendations */
    getRecommendations: async (): Promise<Recommendation[]> => {
        try {
            const data = await fetchJSON<{ ai_recommendations: Recommendation[] }>(`${API_BASE}/business/recommendations`, '/data/business-metrics.json');
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
            const data = await fetchJSON<{ featured_agents: MarketplaceAgent[] }>(`${API_BASE}/marketplace`, '/data/marketplace-agents.json');
            return data.featured_agents || data;
        } catch {
            const data = await fetchJSON<{ featured_agents: MarketplaceAgent[] }>('/data/marketplace-agents.json');
            return data.featured_agents;
        }
    },

    /** Get marketplace categories */
    getCategories: async (): Promise<string[]> => {
        try {
            const data = await fetchJSON<{ categories: string[] }>(`${API_BASE}/marketplace/categories`, '/data/marketplace-agents.json');
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
            const res = await fetch(`${API_BASE}/onboarding/analyze`, {
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
            const res = await fetch(`${API_BASE}/upload`, { 
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
            const res = await fetch(`${API_BASE}/agents/create`, {
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
            const res = await fetch(`${API_BASE}/agents/${id}`, {
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