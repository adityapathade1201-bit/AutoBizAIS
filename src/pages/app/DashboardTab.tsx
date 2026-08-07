import { useEffect, useState } from 'react';
import {
    Building2, Upload, Bot, Wrench, Settings2, Moon, Sun, Globe, Trash2,
    Mail, Calendar, Calculator, FileSpreadsheet, MessageSquare, CreditCard,
    TrendingUp, FileText, BarChart3, Plus, ToggleLeft, ToggleRight, Pencil,
    Instagram, Twitter, ChevronRight, Shield, Database, Download
} from 'lucide-react';
import { useAgentStore } from '../../stores/agentStore';
import { useAppStore } from '../../stores/appStore';
import type { Agent } from '../../types';

const tools = [
    { name: 'Email Manager', icon: Mail, color: '#3b82f6' },
    { name: 'Calendar', icon: Calendar, color: '#10b981' },
    { name: 'Tally Integration', icon: Calculator, color: '#f59e0b' },
    { name: 'Excel Editor', icon: FileSpreadsheet, color: '#22c55e' },
    { name: 'WhatsApp Business', icon: MessageSquare, color: '#25d366' },
    { name: 'Payment Gateway', icon: CreditCard, color: '#8b5cf6' },
    { name: 'Stock Tracker', icon: TrendingUp, color: '#ef4444' },
    { name: 'Invoice Generator', icon: FileText, color: '#06b6d4' },
    { name: 'Report Builder', icon: BarChart3, color: '#ec4899' },
];

const mockDocs = [
    { name: 'Q4 Sales Report.pdf', size: '2.4 MB', date: '2024-02-08' },
    { name: 'Inventory List.xlsx', size: '1.1 MB', date: '2024-02-05' },
    { name: 'Customer Feedback.csv', size: '340 KB', date: '2024-01-28' },
];

export default function DashboardTab() {
    const { agents, fetchAgents } = useAgentStore();
    const { theme, toggleTheme, language, setLanguage } = useAppStore();
    const [agentStatuses, setAgentStatuses] = useState<Record<string, boolean>>({});
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        fetchAgents().then(() => setLoaded(true));
    }, [fetchAgents]);

    useEffect(() => {
        const timer = setTimeout(() => {
            const statuses: Record<string, boolean> = {};
            agents.forEach((a) => { statuses[a.id] = a.status !== 'offline'; });
            setAgentStatuses(statuses);
        }, 0);
        return () => clearTimeout(timer);
    }, [agents]);

    const toggleAgentStatus = (id: string) => {
        setAgentStatuses((prev) => ({ ...prev, [id]: !prev[id] }));
    };

    return (
        <div className="h-full overflow-y-auto scrollbar-thin">
            <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-8">
                {/* Header */}
                <div className={`transition-all duration-500 ${loaded ? 'opacity-100' : 'opacity-0'}`}>
                    <h1 className="text-2xl font-heading font-bold text-gray-900 dark:text-white">Dashboard</h1>
                    <p className="text-sm text-gray-500 mt-1">Manage your workspace and preferences</p>
                </div>

                {/* Section 1: Business Profile */}
                <Section title="Business Profile" icon={Building2}>
                    <div className="grid sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-500 mb-1">Business Name</label>
                            <input type="text" defaultValue="Sharma Electronics" className="input-field" />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-500 mb-1">Industry</label>
                            <input type="text" defaultValue="Retail & E-commerce" className="input-field" />
                        </div>
                        <div className="sm:col-span-2">
                            <label className="block text-sm text-gray-500 mb-1">Description</label>
                            <textarea defaultValue="Electronics retail store selling mobile phones, accessories, and home appliances in Pune, Maharashtra." rows={2} className="input-field resize-none" />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-500 mb-1">Phone</label>
                            <input type="tel" defaultValue="+91 98765 43210" className="input-field" />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-500 mb-1">Email</label>
                            <input type="email" defaultValue="info@sharmaelectronics.in" className="input-field" />
                        </div>
                    </div>
                    <button className="btn-primary mt-4 text-sm px-5 py-2.5">Save Profile</button>
                </Section>

                {/* Section 2: Data Management */}
                <Section title="Data Management" icon={Database}>
                    <div className="border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-2xl p-8 text-center hover:border-blue-400 dark:hover:border-blue-500 transition-colors cursor-pointer"
                        onClick={() => document.getElementById('dash-upload')?.click()}
                    >
                        <Upload className="w-8 h-8 text-gray-400 mx-auto mb-3" />
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Drop files here or click to upload</p>
                        <p className="text-xs text-gray-400 mt-1">PDFs, CSV, Excel, Images</p>
                        <input id="dash-upload" type="file" multiple className="hidden" />
                    </div>

                    {/* Doc List */}
                    <div className="mt-4 space-y-2">
                        {mockDocs.map((doc) => (
                            <div key={doc.name} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                                <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">{doc.name}</div>
                                    <div className="text-xs text-gray-400">{doc.size} • {doc.date}</div>
                                </div>
                                <button className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/20 text-gray-400 hover:text-red-500 transition-colors">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Social Connections */}
                    <div className="mt-4 flex flex-wrap gap-3">
                        <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <Instagram className="w-4 h-4 text-pink-500" />
                            Connect Instagram
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                            <Twitter className="w-4 h-4" />
                            Connect X / Twitter
                        </button>
                    </div>
                </Section>

                {/* Section 3: Agent Controls */}
                <Section title="Agent Controls" icon={Bot}>
                    {/* Build New Agent */}
                    <div className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-2xl border border-blue-200/40 dark:border-blue-700/30 p-5 mb-4">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                                <Plus className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 dark:text-white">Build New Agent</h3>
                                <p className="text-sm text-gray-500">Create a custom AI agent for your needs</p>
                            </div>
                            <ChevronRight className="w-5 h-5 text-gray-400" />
                        </div>
                    </div>

                    {/* Agent Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-left text-gray-500 border-b border-gray-100 dark:border-gray-700">
                                    <th className="pb-3 font-medium">Agent</th>
                                    <th className="pb-3 font-medium hidden sm:table-cell">Model</th>
                                    <th className="pb-3 font-medium text-center">Active</th>
                                    <th className="pb-3 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {agents.map((agent: Agent) => (
                                    <tr key={agent.id} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
                                        <td className="py-3">
                                            <div className="flex items-center gap-2">
                                                <span className="text-lg">{agent.avatar}</span>
                                                <span className="font-medium text-gray-900 dark:text-white">{agent.name}</span>
                                            </div>
                                        </td>
                                        <td className="py-3 hidden sm:table-cell">
                                            <select className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 border-none text-xs font-medium text-gray-600 dark:text-gray-300 outline-none" defaultValue={agent.model || 'gpt-4'}>
                                                <option>gpt-4</option>
                                                <option>gpt-3.5-turbo</option>
                                                <option>claude-3</option>
                                                <option>gemini-pro</option>
                                            </select>
                                        </td>
                                        <td className="py-3 text-center">
                                            <button onClick={() => toggleAgentStatus(agent.id)}>
                                                {agentStatuses[agent.id] ? (
                                                    <ToggleRight className="w-7 h-7 text-green-500" />
                                                ) : (
                                                    <ToggleLeft className="w-7 h-7 text-gray-400" />
                                                )}
                                            </button>
                                        </td>
                                        <td className="py-3 text-right">
                                            <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 transition-colors">
                                                <Pencil className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Section>

                {/* Section 4: Manual Tools */}
                <Section title="Manual Tools" icon={Wrench}>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {tools.map(({ name, icon: Icon, color }) => (
                            <button
                                key={name}
                                className="flex flex-col items-center gap-2 p-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 card-hover text-center"
                            >
                                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
                                    <Icon className="w-5 h-5" style={{ color }} />
                                </div>
                                <span className="text-xs font-medium text-gray-700 dark:text-gray-200">{name}</span>
                            </button>
                        ))}
                    </div>
                </Section>

                {/* Section 5: Settings */}
                <Section title="Settings" icon={Settings2}>
                    <div className="space-y-4">
                        <SettingRow label="Theme" description="Toggle dark / light mode">
                            <button onClick={toggleTheme} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-medium">
                                {theme === 'light' ? <Sun className="w-4 h-4 text-amber-500" /> : <Moon className="w-4 h-4 text-blue-400" />}
                                {theme === 'light' ? 'Light' : 'Dark'}
                            </button>
                        </SettingRow>

                        <SettingRow label="Language" description="Switch between English and Hindi">
                            <button onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-medium">
                                <Globe className="w-4 h-4" />
                                {language === 'en' ? 'English' : 'हिंदी'}
                            </button>
                        </SettingRow>

                        <SettingRow label="API Credits" description="250 / 500 credits remaining">
                            <div className="w-32">
                                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 rounded-full" style={{ width: '50%' }} />
                                </div>
                            </div>
                        </SettingRow>

                        <SettingRow label="Privacy" description="Manage data and privacy settings">
                            <Shield className="w-5 h-5 text-gray-400" />
                        </SettingRow>

                        <SettingRow label="Export Data" description="Download all your data">
                            <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-200 transition-colors">
                                <Download className="w-4 h-4" />
                                Export
                            </button>
                        </SettingRow>

                        <SettingRow label="Clear History" description="Delete all chat history and data">
                            <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-950/20 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-100 transition-colors">
                                <Trash2 className="w-4 h-4" />
                                Clear
                            </button>
                        </SettingRow>
                    </div>
                </Section>

                <div className="h-8" />
            </div>
        </div>
    );
}

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 p-5 sm:p-6 animate-fade-in">
            <div className="flex items-center gap-2 mb-5">
                <Icon className="w-5 h-5 text-gray-500" />
                <h2 className="text-lg font-heading font-bold text-gray-900 dark:text-white">{title}</h2>
            </div>
            {children}
        </div>
    );
}

function SettingRow({ label, description, children }: { label: string; description: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between py-3 border-b border-gray-50 dark:border-gray-800 last:border-0">
            <div>
                <div className="text-sm font-medium text-gray-700 dark:text-gray-200">{label}</div>
                <div className="text-xs text-gray-400">{description}</div>
            </div>
            {children}
        </div>
    );
}
