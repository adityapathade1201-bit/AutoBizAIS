import { useEffect, useState, useRef } from 'react';
import { Send, Paperclip, Mic, IndianRupee, MoreVertical, Search, Plus, Wrench, Bot } from 'lucide-react';
import { useAgentStore } from '../../stores/agentStore';
import { useAppStore } from '../../stores/appStore';
import { wsService } from '../../services/websocket';
import type { Agent, Message } from '../../types';

function AgentAvatar({ agent, size = 'md' }: { agent: Agent; size?: 'sm' | 'md' | 'lg' }) {
    const sizeClasses = { sm: 'w-8 h-8 text-sm', md: 'w-10 h-10 text-lg', lg: 'w-12 h-12 text-xl' };
    return (
        <div
            className={`${sizeClasses[size]} rounded-full flex items-center justify-center flex-shrink-0`}
            style={{ backgroundColor: `${agent.color}20` }}
        >
            {agent.avatar}
        </div>
    );
}

function StatusDot({ status }: { status: string }) {
    const colors: Record<string, string> = { online: 'bg-green-500', busy: 'bg-amber-500', offline: 'bg-gray-400' };
    return <div className={`w-2.5 h-2.5 rounded-full ${colors[status] || colors.offline} ring-2 ring-white dark:ring-gray-900`} />;
}

function ChatBubble({ message, agent }: { message: Message; agent: Agent | null }) {
    const isUser = message.type === 'user';
    const isTool = message.type === 'tool_execution';

    if (isTool) {
        return (
            <div className="flex justify-center my-3 px-4 animate-fade-in">
                <div className="chat-bubble-tool flex items-start gap-2 text-sm">
                    <Wrench className="w-4 h-4 mt-0.5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
                    <div>
                        <div className="font-medium text-amber-800 dark:text-amber-300 text-xs mb-0.5">
                            {message.tool?.replace(/_/g, ' ')?.toUpperCase()}
                        </div>
                        {message.content}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 px-4 animate-slide-up`}>
            <div className={`flex items-end gap-2 max-w-[85%] ${isUser ? 'flex-row-reverse' : ''}`}>
                {!isUser && agent && <AgentAvatar agent={agent} size="sm" />}
                <div>
                    <div className={isUser ? 'chat-bubble-user' : 'chat-bubble-agent'}>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    </div>
                    <div className={`text-[10px] text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left ml-1'}`}>
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function AgentsTab() {
    const { agents, currentAgent, chatHistory, loading, sendingMessage, fetchAgents, setCurrentAgent, sendMessage } = useAgentStore();
    const { language } = useAppStore();
    const [input, setInput] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [showSidebar, setShowSidebar] = useState(true);
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchAgents();
    }, [fetchAgents]);

    // ⚡ REAL-TIME MULTI-DEVICE WEBSOCKET SYNC
    useEffect(() => {
        wsService.connect();

        const unsubscribe = wsService.subscribe((data) => {
            if (data.event === 'NEW_AGENT_MESSAGE') {
                const targetAgentId = data.agentId;
                const storeState = useAgentStore.getState();
                const existingHistory = storeState.chatHistory[targetAgentId] || [];

                // Check for duplicate to prevent double appending
                const lastMsg = existingHistory[existingHistory.length - 1];
                if (lastMsg && lastMsg.content === data.aiReply) {
                    return;
                }

                const updatedMessages: Message[] = [
                    ...existingHistory,
                    {
                        id: `u-${Date.now()}`,
                        type: 'user',
                        content: data.userMessage,
                        timestamp: new Date().toISOString()
                    },
                    {
                        id: `a-${Date.now() + 1}`,
                        type: 'agent',
                        content: data.aiReply,
                        timestamp: new Date().toISOString()
                    }
                ];

                // Update Zustand store so chat updates instantly on screen
                useAgentStore.setState({
                    chatHistory: {
                        ...storeState.chatHistory,
                        [targetAgentId]: updatedMessages
                    }
                });
            }
        });

        return () => unsubscribe();
    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory, currentAgent]);

    const handleSend = () => {
        if (!input.trim() || !currentAgent) return;
        sendMessage(input.trim());
        setInput('');
    };

    const currentMessages = currentAgent ? chatHistory[currentAgent.id] || [] : [];
    const filteredAgents = agents.filter((a) =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="h-full flex">
            {/* Sidebar */}
            <div
                className={`${showSidebar ? 'flex' : 'hidden lg:flex'
                    } flex-col w-full lg:w-80 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900`}
            >
                {/* Sidebar Header */}
                <div className="p-4 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-lg font-heading font-bold text-gray-900 dark:text-white">
                            {language === 'hi' ? 'एजेंट्स' : 'Agents'}
                        </h2>
                        <button className="p-2 rounded-lg bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-950/60 transition-colors">
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={language === 'hi' ? 'एजेंट खोजें...' : 'Search agents...'}
                            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
                        />
                    </div>
                </div>

                {/* Agent List */}
                <div className="flex-1 overflow-y-auto scrollbar-thin">
                    {loading
                        ? Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="flex items-center gap-3 p-4">
                                <div className="skeleton w-10 h-10 rounded-full" />
                                <div className="flex-1">
                                    <div className="skeleton h-4 w-32 mb-2" />
                                    <div className="skeleton h-3 w-48" />
                                </div>
                            </div>
                        ))
                        : filteredAgents.map((agent) => (
                            <button
                                key={agent.id}
                                onClick={() => {
                                    setCurrentAgent(agent);
                                    setShowSidebar(false);
                                }}
                                className={`w-full flex items-center gap-3 p-4 text-left transition-all duration-150 hover:bg-gray-50 dark:hover:bg-gray-800/60 ${currentAgent?.id === agent.id ? 'bg-blue-50/70 dark:bg-blue-950/30' : ''
                                    }`}
                            >
                                <div className="relative">
                                    <AgentAvatar agent={agent} />
                                    <div className="absolute -bottom-0.5 -right-0.5">
                                        <StatusDot status={agent.status} />
                                    </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                            {agent.name}
                                        </span>
                                        {agent.timestamp && (
                                            <span className="text-[10px] text-gray-400 flex-shrink-0 ml-2">
                                                {new Date(agent.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                                        {agent.lastMessage || agent.description}
                                    </p>
                                </div>
                            </button>
                        ))}
                </div>
            </div>

            {/* Chat Area */}
            <div
                className={`${!showSidebar ? 'flex' : 'hidden lg:flex'
                    } flex-col flex-1 bg-gray-50 dark:bg-gray-950`}
            >
                {currentAgent ? (
                    <>
                        {/* Chat Header */}
                        <div className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
                            <button onClick={() => setShowSidebar(true)} className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                            </button>
                            <AgentAvatar agent={currentAgent} />
                            <div className="flex-1 min-w-0">
                                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{currentAgent.name}</h3>
                                <div className="flex items-center gap-1.5">
                                    <StatusDot status={currentAgent.status} />
                                    <span className="text-xs text-gray-500 capitalize">{currentAgent.status}</span>
                                    {currentAgent.model && (
                                        <span className="text-xs text-gray-400 ml-2">• {currentAgent.model}</span>
                                    )}
                                </div>
                            </div>
                            <button className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                <MoreVertical className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto scrollbar-thin py-4" style={{
                            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(0,0,0,0.03) 1px, transparent 0)',
                            backgroundSize: '20px 20px',
                        }}>
                            {currentMessages.length === 0 && (
                                <div className="flex flex-col items-center justify-center h-full text-center px-6">
                                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mb-4" style={{ backgroundColor: `${currentAgent.color}15` }}>
                                        {currentAgent.avatar}
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-1">{currentAgent.name}</h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs">{currentAgent.description}</p>
                                    <p className="text-xs text-gray-400 mt-2">Send a message to get started</p>
                                </div>
                            )}
                            {currentMessages.map((msg) => (
                                <ChatBubble key={msg.id} message={msg} agent={currentAgent} />
                            ))}
                            {sendingMessage && (
                                <div className="flex justify-start mb-3 px-4">
                                    <div className="flex items-end gap-2">
                                        <AgentAvatar agent={currentAgent} size="sm" />
                                        <div className="chat-bubble-agent flex gap-1 py-3">
                                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>

                        {/* Input Bar */}
                        <div className="px-4 py-3 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
                            <div className="flex items-end gap-2">
                                <button className="p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0">
                                    <Paperclip className="w-5 h-5" />
                                </button>
                                <div className="flex-1 relative">
                                    <textarea
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                                        placeholder={language === 'hi' ? 'संदेश लिखें...' : 'Type a message...'}
                                        rows={1}
                                        className="w-full px-4 py-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all resize-none"
                                        style={{ minHeight: 40, maxHeight: 120 }}
                                    />
                                </div>
                                <button className="p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0">
                                    <Mic className="w-5 h-5" />
                                </button>
                                <button className="p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0">
                                    <IndianRupee className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={handleSend}
                                    disabled={!input.trim()}
                                    className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all flex-shrink-0"
                                >
                                    <Send className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center px-6">
                            <div className="w-20 h-20 rounded-3xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center mx-auto mb-5">
                                <Bot className="w-10 h-10 text-blue-500" />
                            </div>
                            <h3 className="text-xl font-heading font-bold text-gray-700 dark:text-gray-200 mb-2">
                                {language === 'hi' ? 'एजेंट चुनें' : 'Select an Agent'}
                            </h3>
                            <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                {language === 'hi'
                                    ? 'बातचीत शुरू करने के लिए बाईं ओर से एजेंट चुनें'
                                    : 'Choose an agent from the sidebar to start a conversation'}
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}