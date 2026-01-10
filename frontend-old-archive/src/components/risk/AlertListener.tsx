'use client';

import { useEffect } from 'react';
import { alertWS } from '@/lib/ws_alerts';
import toast from 'react-hot-toast';
import { AlertTriangle, Info, XCircle, ShieldAlert } from 'lucide-react';

export default function AlertListener() {
    useEffect(() => {
        // Connect to WebSocket on mount
        alertWS.connect();

        const handleAlert = (alert: any) => {
            const type = alert.type || 'INFO';

            const icon = type === 'CRITICAL' ? <XCircle className="w-6 h-6 text-red-500" /> :
                type === 'WARNING' ? <AlertTriangle className="w-6 h-6 text-yellow-500" /> :
                    <Info className="w-6 h-6 text-blue-500" />;

            const bgColor = type === 'CRITICAL' ? 'bg-red-50 dark:bg-red-900/20' :
                type === 'WARNING' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
                    'bg-blue-50 dark:bg-blue-900/20';

            const borderColor = type === 'CRITICAL' ? 'border-red-200 dark:border-red-800' :
                type === 'WARNING' ? 'border-yellow-200 dark:border-yellow-800' :
                    'border-blue-200 dark:border-blue-800';

            toast.custom((t) => (
                <div
                    className={`${t.visible ? 'animate-enter' : 'animate-leave'
                        } max-w-md w-full ${bgColor} border ${borderColor} shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
                >
                    <div className="flex-1 w-0 p-4">
                        <div className="flex items-start">
                            <div className="flex-shrink-0 pt-0.5">
                                {icon}
                            </div>
                            <div className="ml-3 flex-1">
                                <p className={`text-sm font-medium ${type === 'CRITICAL' ? 'text-red-800 dark:text-red-200' :
                                        type === 'WARNING' ? 'text-yellow-800 dark:text-yellow-200' :
                                            'text-blue-800 dark:text-blue-200'
                                    }`}>
                                    {alert.title}
                                </p>
                                <p className={`mt-1 text-sm ${type === 'CRITICAL' ? 'text-red-700 dark:text-red-300' :
                                        type === 'WARNING' ? 'text-yellow-700 dark:text-yellow-300' :
                                            'text-blue-700 dark:text-blue-300'
                                    }`}>
                                    {alert.message}
                                </p>
                                {alert.symbol && (
                                    <p className="mt-1 text-xs text-gray-500">
                                        Symbol: {alert.symbol}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="flex border-l border-gray-200 dark:border-gray-700">
                        <button
                            onClick={() => toast.dismiss(t.id)}
                            className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                            Close
                        </button>
                    </div>
                </div>
            ), {
                duration: type === 'CRITICAL' ? Infinity : 5000,
                position: 'top-right',
            });

            // Play sound for critical alerts
            if (type === 'CRITICAL') {
                const audio = new Audio('/sounds/critical_alert.mp3'); // We assume this exists or fails silently
                audio.play().catch(() => { });
            }
        };

        alertWS.addListener(handleAlert);

        return () => {
            alertWS.removeListener(handleAlert);
        };
    }, []);

    return null;
}
