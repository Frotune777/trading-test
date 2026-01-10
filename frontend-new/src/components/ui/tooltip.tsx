'use client';

/**
 * Tooltip Component
 * Displays detailed pillar-by-pillar reasoning breakdown
 */

import React, { useState } from 'react';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TooltipProps {
    content: React.ReactNode;
    children: React.ReactNode;
    className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div className="relative inline-block">
            <div
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                className="cursor-help"
            >
                {children}
            </div>
            {isVisible && (
                <div
                    className={cn(
                        "absolute z-50 w-80 p-4 bg-popover text-popover-foreground rounded-lg shadow-lg border border-border",
                        "bottom-full left-1/2 transform -translate-x-1/2 mb-2",
                        "animate-in fade-in-0 zoom-in-95",
                        className
                    )}
                >
                    {content}
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
                        <div className="w-2 h-2 bg-popover border-r border-b border-border transform rotate-45"></div>
                    </div>
                </div>
            )}
        </div>
    );
}
