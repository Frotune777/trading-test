'use client';

import Link from 'next/link';
import { Activity, Code2, TrendingUp, BarChart3, Shield, Brain } from 'lucide-react';

export default function HomePage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center p-6">
            <div className="max-w-4xl w-full">
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-bold text-white mb-4">
                        QUAD Trading Platform
                    </h1>
                    <p className="text-xl text-gray-300">
                        Advanced TA Aggregator & Strategy Management
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* QUAD Intelligence Card */}
                    <Link href="/analytics">
                        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 hover:bg-white/20 transition-all cursor-pointer border border-white/20 group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10 scale-150 rotate-12 group-hover:scale-[2] transition-transform">
                                <Brain className="w-12 h-12 text-blue-400" />
                            </div>
                            <div className="flex items-center gap-4 mb-4">
                                <div className="p-3 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                    <Brain className="w-8 h-8 text-blue-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">QUAD Intelligence</h2>
                            </div>
                            <p className="text-gray-300 mb-4">
                                Advanced AI analytics, Insider Sentinel, and model accuracy breakdown
                            </p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li>• Insider trading & smart money footprints</li>
                                <li>• Sector peer performance ranking</li>
                                <li>• ML prediction confidence metrics</li>
                            </ul>
                        </div>
                    </Link>

                    {/* TA Dashboard Card */}
                    <Link href="/ta-dashboard">
                        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 hover:bg-white/20 transition-all cursor-pointer border border-white/20 group">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="p-3 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                                    <Activity className="w-8 h-8 text-blue-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">TA Aggregator</h2>
                            </div>
                            <p className="text-gray-300 mb-4">
                                Monitor signal accuracy, configure regime weights, and analyze indicator performance
                            </p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li>• Historical accuracy tracking</li>
                                <li>• Regime-specific weight configuration</li>
                                <li>• Indicator performance breakdown</li>
                            </ul>
                        </div>
                    </Link>

                    {/* Strategy Management Card */}
                    <Link href="/strategies">
                        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 hover:bg-white/20 transition-all cursor-pointer border border-white/20 group">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="p-3 bg-purple-500/20 rounded-lg group-hover:bg-purple-500/30 transition-colors">
                                    <Code2 className="w-8 h-8 text-purple-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">Strategies</h2>
                            </div>
                            <p className="text-gray-300 mb-4">
                                Create, edit, and backtest custom trading strategies with Python
                            </p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li>• Monaco code editor with validation</li>
                                <li>• Strategy templates (SMA, RSI, MACD)</li>
                                <li>• Comprehensive backtesting</li>
                            </ul>
                        </div>
                    </Link>

                    {/* Decision Ledger Card */}
                    <Link href="/decisions">
                        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 hover:bg-white/20 transition-all cursor-pointer border border-white/20 group">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="p-3 bg-green-500/20 rounded-lg group-hover:bg-green-500/30 transition-colors">
                                    <Activity className="w-8 h-8 text-green-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">Decision Ledger</h2>
                            </div>
                            <p className="text-gray-300 mb-4">
                                Audit trail of all trading decisions with causal explainability
                            </p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li>• Immutable decision records</li>
                                <li>• Causal graph visualization</li>
                                <li>• Conviction timeline tracking</li>
                            </ul>
                        </div>
                    </Link>

                    {/* Risk Command Center Card */}
                    <Link href="/risk">
                        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 hover:bg-white/20 transition-all cursor-pointer border border-white/20 group">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="p-3 bg-red-500/20 rounded-lg group-hover:bg-red-500/30 transition-colors">
                                    <Shield className="w-8 h-8 text-red-400" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">Risk Command</h2>
                            </div>
                            <p className="text-gray-300 mb-4">
                                Centralized risk monitoring, limit enforcement, and emergency controls
                            </p>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li>• Real-time P&L & Exposure tracking</li>
                                <li>• Global Kill Switch & Limits Config</li>
                                <li>• Automated Risk Alerts</li>
                            </ul>
                        </div>
                    </Link>
                </div>

                {/* Features Grid */}
                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
                        <TrendingUp className="w-6 h-6 text-green-400 mb-3" />
                        <h3 className="text-white font-semibold mb-2">Real-time Analysis</h3>
                        <p className="text-sm text-gray-400">
                            Live signal generation with confidence scores
                        </p>
                    </div>
                    <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
                        <BarChart3 className="w-6 h-6 text-blue-400 mb-3" />
                        <h3 className="text-white font-semibold mb-2">Performance Metrics</h3>
                        <p className="text-sm text-gray-400">
                            Track accuracy and optimize weights
                        </p>
                    </div>
                    <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
                        <Code2 className="w-6 h-6 text-purple-400 mb-3" />
                        <h3 className="text-white font-semibold mb-2">Custom Strategies</h3>
                        <p className="text-sm text-gray-400">
                            Build and test your own algorithms
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-12 text-center text-gray-400 text-sm">
                    <p>Phase 3.5: Advanced Analytics Implementation Complete</p>
                    <p className="mt-2">Backend: 240+ endpoints | Frontend: 12 components</p>
                </div>
            </div>
        </div>
    );
}
