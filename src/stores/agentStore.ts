import { create } from 'zustand';
import type { Agent, Message } from '../types';
import { api } from '../services/api';

interface AgentState {
    agents: Agent[];
    currentAgent: Agent | null;
    chatHistory: Record<string, Message[]>;
    loading: boolean;
    sendingMessage: boolean;

    // Actions
    fetchAgents: () => Promise<void>;
    setCurrentAgent: (agent: Agent) => void;
    fetchChatHistory: (agentId: string) => Promise<void>;
    sendMessage: (message: string) => Promise<void>;
    addAgent: (agent: Agent) => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
    agents: [],
    currentAgent: null,
    chatHistory: {},
    loading: false,
    sendingMessage: false,

    fetchAgents: async () => {
        set({ loading: true });
        try {
            const agents = await api.getAgents();
            set({ agents, loading: false });
        } catch {
            set({ loading: false });
        }
    },

    setCurrentAgent: (agent) => {
        set({ currentAgent: agent });
        get().fetchChatHistory(agent.id);
    },

    fetchChatHistory: async (agentId) => {
        try {
            const conversation = await api.getChatHistory(agentId);
            if (conversation) {
                set((state) => ({
                    chatHistory: { ...state.chatHistory, [agentId]: conversation.messages },
                }));
            }
        } catch {
            // silently fail
        }
    },

    sendMessage: async (message) => {
        const { currentAgent, chatHistory } = get();
        if (!currentAgent) return;

        const userMsg: Message = {
            id: `user-${Date.now()}`,
            type: 'user',
            content: message,
            timestamp: new Date().toISOString(),
        };

        const currentMessages = chatHistory[currentAgent.id] || [];
        set({
            chatHistory: {
                ...chatHistory,
                [currentAgent.id]: [...currentMessages, userMsg],
            },
            sendingMessage: true,
        });

        try {
            const response = await api.sendMessage(currentAgent.id, message);
            const agentMsg: Message = {
                id: `agent-${Date.now()}`,
                type: 'agent',
                content: response.reply,
                timestamp: new Date().toISOString(),
            };

            set((state) => ({
                chatHistory: {
                    ...state.chatHistory,
                    [currentAgent.id]: [...(state.chatHistory[currentAgent.id] || []), agentMsg],
                },
                sendingMessage: false,
            }));
        } catch (error) {
            const errorMsg: Message = {
                id: `error-${Date.now()}`,
                type: 'agent',
                content: error instanceof Error
                    ? `⚠️ ${error.message}`
                    : '⚠️ The request failed. Check the backend connection and server logs.',
                timestamp: new Date().toISOString(),
            };
            set((state) => ({
                chatHistory: {
                    ...state.chatHistory,
                    [currentAgent.id]: [...(state.chatHistory[currentAgent.id] || []), errorMsg],
                },
                sendingMessage: false,
            }));
        }
    },

    addAgent: (agent) => {
        set((state) => ({ agents: [...state.agents, agent] }));
    },
}));
