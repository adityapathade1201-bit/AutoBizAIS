import { useEffect, useState } from 'react';
import { Search, Star, Download, Filter, Share2, Plus } from 'lucide-react';
import { api } from '../../services/api';
import type { MarketplaceAgent } from '../../types';

const priceFilters = ['All', 'Free', 'Paid'];

export default function CommunityTab() {
    const [agents, setAgents] = useState<MarketplaceAgent[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [search, setSearch] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [selectedPrice, setSelectedPrice] = useState('All');
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        Promise.all([api.getMarketplaceAgents(), api.getCategories()]).then(([a, c]) => {
            setAgents(a);
            setCategories(c);
            setTimeout(() => setLoaded(true), 100);
        });
    }, []);

    const filtered = agents.filter((a) => {
        const matchSearch = a.name.toLowerCase().includes(search.toLowerCase()) ||
            a.description.toLowerCase().includes(search.toLowerCase()) ||
            a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
        const matchCategory = selectedCategory === 'All' || a.category === selectedCategory;
        const matchPrice = selectedPrice === 'All' ||
            (selectedPrice === 'Free' && a.price === 'free') ||
            (selectedPrice === 'Paid' && a.price !== 'free');
        return matchSearch && matchCategory && matchPrice;
    });

    const featured = agents.filter((a) => a.featured);

    return (
        <div className="h-full overflow-y-auto scrollbar-thin">
            <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
                {/* Header */}
                <div className={`flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4 transition-all duration-500 ${loaded ? 'opacity-100' : 'opacity-0'}`}>
                    <div>
                        <h1 className="text-2xl font-heading font-bold text-gray-900 dark:text-white">Agent Marketplace</h1>
                        <p className="text-sm text-gray-500 mt-1">Discover agents built for Indian businesses</p>
                    </div>
                    <button className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold shadow-md shadow-blue-500/20 hover:shadow-lg transition-all">
                        <Share2 className="w-4 h-4" />
                        Share Your Agent
                    </button>
                </div>

                {/* Search & Filters */}
                <div className={`mb-8 space-y-4 transition-all duration-500 delay-100 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search for agents, categories, or tags..."
                            className="input-field pl-12 py-3.5 text-base"
                        />
                    </div>

                    <div className="flex flex-wrap gap-3">
                        {/* Category Filter */}
                        <div className="flex items-center gap-2">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <div className="flex gap-1.5 flex-wrap">
                                <button
                                    onClick={() => setSelectedCategory('All')}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedCategory === 'All' ? 'bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}
                                >
                                    All
                                </button>
                                {categories.map((cat) => (
                                    <button
                                        key={cat}
                                        onClick={() => setSelectedCategory(cat)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedCategory === cat ? 'bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}
                                    >
                                        {cat}
                                    </button>
                                ))}
                            </div>
                        </div>
                        {/* Price Filter */}
                        <div className="flex gap-1.5">
                            {priceFilters.map((p) => (
                                <button
                                    key={p}
                                    onClick={() => setSelectedPrice(p)}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${selectedPrice === p ? 'bg-green-100 dark:bg-green-950/40 text-green-600 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'}`}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Featured Section */}
                {featured.length > 0 && !search && selectedCategory === 'All' && (
                    <div className={`mb-8 transition-all duration-500 delay-150 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                        <h2 className="text-lg font-heading font-bold text-gray-900 dark:text-white mb-4">⭐ Top Agents This Week</h2>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {featured.map((agent) => (
                                <AgentCard key={agent.id} agent={agent} featured />
                            ))}
                        </div>
                    </div>
                )}

                {/* All Agents Grid */}
                <div className={`transition-all duration-500 delay-200 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                    <h2 className="text-lg font-heading font-bold text-gray-900 dark:text-white mb-4">
                        {search || selectedCategory !== 'All' ? `Results (${filtered.length})` : 'All Agents'}
                    </h2>
                    {filtered.length === 0 ? (
                        <div className="text-center py-16">
                            <p className="text-gray-500">No agents found matching your search.</p>
                        </div>
                    ) : (
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                            {filtered.map((agent) => (
                                <AgentCard key={agent.id} agent={agent} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function AgentCard({ agent, featured = false }: { agent: MarketplaceAgent; featured?: boolean }) {
    const [added, setAdded] = useState(false);

    return (
        <div className={`bg-white dark:bg-gray-800 rounded-2xl border ${featured ? 'border-amber-200 dark:border-amber-800/30' : 'border-gray-100 dark:border-gray-700'} p-5 card-hover flex flex-col`}>
            {/* Header */}
            <div className="flex items-start gap-3 mb-3">
                <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
                    style={{ backgroundColor: `${agent.color}15` }}
                >
                    {agent.avatar}
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">{agent.name}</h3>
                    <p className="text-xs text-gray-500 truncate">{agent.creator}</p>
                </div>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2 flex-1">{agent.description}</p>

            {/* Tags */}
            <div className="flex flex-wrap gap-1.5 mb-3">
                {agent.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-[10px] text-gray-500 dark:text-gray-400">
                        #{tag}
                    </span>
                ))}
            </div>

            {/* Bottom Row */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{agent.rating}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                        <Download className="w-3 h-3" />
                        {agent.downloads?.toLocaleString()}
                    </div>
                </div>
                <div className="text-sm font-semibold">
                    {agent.price === 'free' ? (
                        <span className="text-green-600 dark:text-green-400">Free</span>
                    ) : (
                        <span className="text-gray-700 dark:text-gray-200">₹{agent.price}/mo</span>
                    )}
                </div>
            </div>

            {/* Action */}
            <button
                onClick={() => setAdded(!added)}
                className={`mt-3 w-full flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${added
                        ? 'bg-green-50 dark:bg-green-950/30 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-800'
                        : 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 hover:bg-blue-100'
                    }`}
            >
                <Plus className="w-4 h-4" />
                {added ? 'Added to Workspace' : 'Add to Workspace'}
            </button>
        </div>
    );
}
