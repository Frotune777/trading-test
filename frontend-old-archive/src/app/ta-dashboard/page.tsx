'use client';

import { useState } from 'react';
import TAAccuracyChart from '@/components/quad/TAAccuracyChart';
import TAIndicatorPerformance from '@/components/quad/TAIndicatorPerformance';
import RegimeWeightsConfig from '@/components/quad/RegimeWeightsConfig';
import { Activity } from 'lucide-react';

export default function TADashboardPage() {
    const [accuracyDays, setAccuracyDays] = useState(30);

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                            <Activity className="w-8 h-8 text-blue-600" />
                            TA Aggregator Dashboard
                        </h1>
                        <p className="text-gray-600 dark:text-gray-400 mt-2">
                            Monitor and configure adaptive technical analysis signals
                        </p>
                    </div>
                    <select
                        value={accuracyDays}
                        onChange={(e) => setAccuracyDays(Number(e.target.value))}
                        className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                    >
                        <option value={7}>Last 7 days</option>
                        <option value={30}>Last 30 days</option>
                        <option value={90}>Last 90 days</option>
                    </select>
                </div>

                {/* Accuracy Chart */}
                <section>
                    <TAAccuracyChart days={accuracyDays} />
                </section>

                {/* Indicator Performance */}
                <section>
                    <TAIndicatorPerformance />
                </section>

                {/* Regime Weights Configuration */}
                <section>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                        Regime Weight Configuration
                    </h2>
                    <RegimeWeightsConfig />
                </section>
            </div>
        </div>
    );
}
