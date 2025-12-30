'use client';

import { TrendingUp, TrendingDown, Activity, Zap, HelpCircle } from 'lucide-react';

export type MarketRegime = 'TRENDING_UP' | 'TRENDING_DOWN' | 'RANGING' | 'VOLATILE' | 'UNKNOWN';

interface RegimeIndicatorProps {
    regime: MarketRegime;
    className?: string;
}

const REGIME_CONFIG: Record<MarketRegime, {
    color: string;
    bgColor: string;
    icon: React.ReactNode;
    label: string;
    description: string;
}> = {
    TRENDING_UP: {
        color: 'text-green-700 dark:text-green-400',
        bgColor: 'bg-green-100 dark:bg-green-900/30',
        icon: <TrendingUp className="w-4 h-4" />,
        label: 'Trending Up',
        description: 'Strong upward trend detected',
    },
    TRENDING_DOWN: {
        color: 'text-red-700 dark:text-red-400',
        bgColor: 'bg-red-100 dark:bg-red-900/30',
        icon: <TrendingDown className="w-4 h-4" />,
        label: 'Trending Down',
        description: 'Strong downward trend detected',
    },
    RANGING: {
        color: 'text-yellow-700 dark:text-yellow-400',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
        icon: <Activity className="w-4 h-4" />,
        label: 'Ranging',
        description: 'Sideways movement, no clear trend',
    },
    VOLATILE: {
        color: 'text-orange-700 dark:text-orange-400',
        bgColor: 'bg-orange-100 dark:bg-orange-900/30',
        icon: <Zap className="w-4 h-4" />,
        label: 'Volatile',
        description: 'High volatility detected',
    },
    UNKNOWN: {
        color: 'text-gray-700 dark:text-gray-400',
        bgColor: 'bg-gray-100 dark:bg-gray-800',
        icon: <HelpCircle className="w-4 h-4" />,
        label: 'Unknown',
        description: 'Regime not determined',
    },
};

export default function RegimeIndicator({ regime, className = '' }: RegimeIndicatorProps) {
    const config = REGIME_CONFIG[regime] || REGIME_CONFIG.UNKNOWN;

    return (
        <div className={`inline-flex items-center gap-2 ${className}`}>
            <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bgColor} ${config.color} font-medium text-sm`}
                title={config.description}
            >
                {config.icon}
                <span>{config.label}</span>
            </div>
        </div>
    );
}

// Export regime config for use in other components
export { REGIME_CONFIG };
