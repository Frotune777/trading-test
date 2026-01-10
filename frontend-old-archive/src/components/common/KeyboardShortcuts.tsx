'use client';

import { useEffect, useCallback } from 'react';
import { addBreadcrumb } from '@/lib/sentry';

interface KeyboardShortcut {
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    meta?: boolean;
    action: () => void;
    description: string;
}

interface UseKeyboardShortcutsProps {
    shortcuts: KeyboardShortcut[];
    enabled?: boolean;
}

/**
 * Hook for registering keyboard shortcuts
 */
export function useKeyboardShortcuts({ shortcuts, enabled = true }: UseKeyboardShortcutsProps) {
    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (!enabled) return;

            for (const shortcut of shortcuts) {
                const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
                const ctrlMatches = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
                const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
                const altMatches = shortcut.alt ? event.altKey : !event.altKey;
                const metaMatches = shortcut.meta ? event.metaKey : !event.metaKey;

                if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
                    event.preventDefault();
                    event.stopPropagation();

                    addBreadcrumb(`Keyboard shortcut: ${shortcut.description}`, 'user-action');
                    shortcut.action();
                    break;
                }
            }
        },
        [shortcuts, enabled]
    );

    useEffect(() => {
        if (enabled) {
            window.addEventListener('keydown', handleKeyDown);
            return () => window.removeEventListener('keydown', handleKeyDown);
        }
    }, [handleKeyDown, enabled]);
}

/**
 * Global keyboard shortcuts component
 */
export function KeyboardShortcuts() {
    // This component doesn't render anything, it just registers global shortcuts
    // Specific shortcuts are registered in components that need them
    return null;
}

export default KeyboardShortcuts;
