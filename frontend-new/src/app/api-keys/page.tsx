'use client';

import { useState } from 'react';
import { useAuth } from '@/context/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Copy, Download, AlertTriangle, Key, RefreshCw } from 'lucide-react';
import MainLayout from '@/components/layout/main-layout';

export default function APIKeysPage() {
    const { user, apiKey, generateApiKey } = useAuth();
    const [loading, setLoading] = useState(false);
    const [showKey, setShowKey] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleGenerateKey = async () => {
        if (!confirm('⚠️ WARNING: Generating a new API key will invalidate your current key. Continue?')) {
            return;
        }

        setLoading(true);
        try {
            await generateApiKey();
            setShowKey(true);
            alert('✅ New API key generated successfully! Make sure to save it now.');
        } catch (error: any) {
            alert(`❌ Failed to generate API key: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        if (apiKey) {
            navigator.clipboard.writeText(apiKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleDownload = () => {
        if (apiKey) {
            const blob = new Blob([`QUAD Trading Platform API Key\n\nUsername: ${user?.username}\nAPI Key: ${apiKey}\n\nGenerated: ${new Date().toISOString()}\n\n⚠️ Keep this key secure! It will not be shown again.`], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `quad-api-key-${user?.username}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    return (
        <MainLayout>
            <div className="p-6 max-w-4xl mx-auto space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">API Key Management</h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Manage your API keys for programmatic access
                    </p>
                </div>

                {/* Warning Banner */}
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-yellow-800 dark:text-yellow-200">
                        <p className="font-semibold">Important Security Information</p>
                        <ul className="mt-2 list-disc list-inside space-y-1">
                            <li>API keys are shown only once. Save them immediately.</li>
                            <li>Generating a new key will invalidate the previous one.</li>
                            <li>Never share your API key or commit it to version control.</li>
                            <li>Use environment variables to store keys in your applications.</li>
                        </ul>
                    </div>
                </div>

                {/* Current API Key */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Key className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                            <h2 className="text-xl font-semibold">Current API Key</h2>
                        </div>
                        <Button
                            onClick={handleGenerateKey}
                            disabled={loading}
                            variant="outline"
                            size="sm"
                        >
                            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                            Generate New Key
                        </Button>
                    </div>

                    {apiKey ? (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">API Key</label>
                                <div className="flex gap-2">
                                    <Input
                                        type={showKey ? 'text' : 'password'}
                                        value={apiKey}
                                        readOnly
                                        className="font-mono text-sm"
                                    />
                                    <Button
                                        onClick={() => setShowKey(!showKey)}
                                        variant="outline"
                                        size="sm"
                                    >
                                        {showKey ? 'Hide' : 'Show'}
                                    </Button>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button
                                    onClick={handleCopy}
                                    variant="outline"
                                    size="sm"
                                >
                                    <Copy className="w-4 h-4 mr-2" />
                                    {copied ? 'Copied!' : 'Copy to Clipboard'}
                                </Button>
                                <Button
                                    onClick={handleDownload}
                                    variant="outline"
                                    size="sm"
                                >
                                    <Download className="w-4 h-4 mr-2" />
                                    Download as File
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            <Key className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>No API key generated yet</p>
                            <p className="text-sm mt-2">Click "Generate New Key" to create one</p>
                        </div>
                    )}
                </div>

                {/* User Information */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                    <h2 className="text-xl font-semibold">Account Information</h2>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p className="text-gray-600 dark:text-gray-400">Username</p>
                            <p className="font-medium">{user?.username}</p>
                        </div>
                        <div>
                            <p className="text-gray-600 dark:text-gray-400">Email</p>
                            <p className="font-medium">{user?.email || 'Not provided'}</p>
                        </div>
                        <div>
                            <p className="text-gray-600 dark:text-gray-400">Order Mode</p>
                            <p className="font-medium capitalize">{user?.order_mode.replace('_', ' ')}</p>
                        </div>
                        <div>
                            <p className="text-gray-600 dark:text-gray-400">Account Status</p>
                            <p className="font-medium">{user?.is_active ? '✅ Active' : '❌ Inactive'}</p>
                        </div>
                    </div>
                </div>

                {/* Usage Example */}
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
                    <h2 className="text-xl font-semibold">Usage Example</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Use your API key in the Authorization header:
                    </p>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded text-sm overflow-x-auto">
                        {`// JavaScript/TypeScript
const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY_HERE'
  }
});

// Python
import requests
headers = {'Authorization': 'Bearer YOUR_API_KEY_HERE'}
response = requests.get('http://localhost:8000/api/v1/auth/me', headers=headers)`}
                    </pre>
                </div>
            </div>
        </MainLayout>
    );
}
