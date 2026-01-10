'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Search, X, Command, ArrowRight, Zap, Home, TrendingUp, Shield, BarChart3, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useKeyboardShortcuts } from './KeyboardShortcuts';
import { addBreadcrumb } from '@/lib/sentry';

interface CommandItem {
    id: string;
    label: string;
    description?: string;
    icon?: React.ReactNode;
    action: () => void;
    category: 'navigation' | 'action' | 'search';
    keywords?: string[];
}

export function CommandPalette() {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const router = useRouter();

    // Define all available commands
    const commands: CommandItem[] = useMemo(() => [
        // Navigation
        {
            id: 'nav-home',
            label: 'Go to Dashboard',
            description: 'View main dashboard',
            icon: <Home className="w-4 h-4" />,
            action: () => router.push('/'),
            category: 'navigation',
            keywords: ['home', 'dashboard', 'main'],
        },
        {
            id: 'nav-analytics',
            label: 'Go to Analytics',
            description: 'View analytics dashboard',
            icon: <BarChart3 className="w-4 h-4" />,
            action: () => router.push('/analytics'),
            category: 'navigation',
            keywords: ['analytics', 'charts', 'insights'],
        },
        {
            id: 'nav-strategies',
            label: 'Go to Strategies',
            description: 'Manage trading strategies',
            icon: <TrendingUp className="w-4 h-4" />,
            action: () => router.push('/strategies'),
            category: 'navigation',
            keywords: ['strategies', 'trading', 'backtest'],
        },
        {
            id: 'nav-risk',
            label: 'Go to Risk Control',
            description: 'View risk dashboard',
            icon: <Shield className="w-4 h-4" />,
            action: () => router.push('/risk'),
            category: 'navigation',
            keywords: ['risk', 'control', 'limits', 'kill switch'],
        },
        {
            id: 'nav-decisions',
            label: 'Go to Decisions',
            description: 'View decision history',
            icon: <Zap className="w-4 h-4" />,
            action: () => router.push('/decisions'),
            category: 'navigation',
            keywords: ['decisions', 'history', 'quad'],
        },
        {
            id: 'nav-ta',
            label: 'Go to TA Dashboard',
            description: 'View technical analysis',
            icon: <TrendingUp className="w-4 h-4" />,
            action: () => router.push('/ta-dashboard'),
            category: 'navigation',
            keywords: ['ta', 'technical', 'analysis', 'indicators'],
        },
        // Actions
        {
            id: 'action-refresh',
            label: 'Refresh Data',
            description: 'Reload all data from server',
            icon: <Zap className="w-4 h-4" />,
            action: () => {
                window.location.reload();
            },
            category: 'action',
            keywords: ['refresh', 'reload', 'update'],
        },
        {
            id: 'action-theme',
            label: 'Toggle Theme',
            description: 'Switch between light and dark mode',
            icon: <Settings className="w-4 h-4" />,
            action: () => {
                document.documentElement.classList.toggle('dark');
            },
            category: 'action',
            keywords: ['theme', 'dark', 'light', 'mode'],
        },
    ], [router]);

    // Fuzzy search filter
    const filteredCommands = useMemo(() => {
        if (!search.trim()) return commands;

        const searchLower = search.toLowerCase();
        return commands.filter(cmd => {
            const labelMatch = cmd.label.toLowerCase().includes(searchLower);
            const descMatch = cmd.description?.toLowerCase().includes(searchLower);
            const keywordMatch = cmd.keywords?.some(k => k.includes(searchLower));
            return labelMatch || descMatch || keywordMatch;
        });
    }, [commands, search]);

    // Group commands by category
    const groupedCommands = useMemo(() => {
        const groups: Record<string, CommandItem[]> = {
            navigation: [],
            action: [],
            search: [],
        };

        filteredCommands.forEach(cmd => {
            groups[cmd.category].push(cmd);
        });

        return groups;
    }, [filteredCommands]);

    // Handle command execution
    const executeCommand = useCallback((command: CommandItem) => {
        addBreadcrumb(`Command palette: ${command.label}`, 'user-action');
        command.action();
        setIsOpen(false);
        setSearch('');
        setSelectedIndex(0);
    }, []);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (filteredCommands[selectedIndex]) {
                    executeCommand(filteredCommands[selectedIndex]);
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                setIsOpen(false);
                setSearch('');
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, filteredCommands, selectedIndex, executeCommand]);

    // Register Cmd+K shortcut
    useKeyboardShortcuts({
        shortcuts: [
            {
                key: 'k',
                ctrl: true,
                action: () => setIsOpen(prev => !prev),
                description: 'Toggle command palette',
            },
        ],
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-2xl mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                {/* Search Input */}
                <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-200 dark:border-gray-700">
                    <Search className="w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Type a command or search..."
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setSelectedIndex(0);
                        }}
                        autoFocus
                        className="flex-1 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                        <Command className="w-3 h-3" />
                        <span>K</span>
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                    >
                        <X className="w-4 h-4 text-gray-400" />
                    </button>
                </div>

                {/* Commands List */}
                <div className="max-h-[60vh] overflow-y-auto">
                    {filteredCommands.length === 0 ? (
                        <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                            No commands found
                        </div>
                    ) : (
                        <>
                            {Object.entries(groupedCommands).map(([category, items]) => {
                                if (items.length === 0) return null;

                                return (
                                    <div key={category}>
                                        <div className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            {category}
                                        </div>
                                        {items.map((cmd, idx) => {
                                            const globalIndex = filteredCommands.indexOf(cmd);
                                            const isSelected = globalIndex === selectedIndex;

                                            return (
                                                <button
                                                    key={cmd.id}
                                                    onClick={() => executeCommand(cmd)}
                                                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                                                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${isSelected
                                                            ? 'bg-indigo-50 dark:bg-indigo-900/20'
                                                            : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                                                        }`}
                                                >
                                                    <div className={`flex-shrink-0 ${isSelected ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-400'}`}>
                                                        {cmd.icon}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className={`font-medium ${isSelected ? 'text-indigo-900 dark:text-indigo-100' : 'text-gray-900 dark:text-white'}`}>
                                                            {cmd.label}
                                                        </div>
                                                        {cmd.description && (
                                                            <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                                                {cmd.description}
                                                            </div>
                                                        )}
                                                    </div>
                                                    {isSelected && (
                                                        <ArrowRight className="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                );
                            })}
                        </>
                    )}
                </div>

                {/* Footer */}
                <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">↑↓</kbd>
                            Navigate
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">↵</kbd>
                            Select
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">Esc</kbd>
                            Close
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CommandPalette;
