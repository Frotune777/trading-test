'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { strategyApi, type StrategyCode, type CodeValidation } from '@/lib/api/strategy';
import Editor from '@monaco-editor/react';
import { Save, Play, AlertTriangle, CheckCircle2, Code2, Info, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

const CODE_TEMPLATES = {
    sma_crossover: `class SMACrossover(StrategyBase):
    """Simple Moving Average Crossover Strategy"""
    
    def setup(self):
        self.sma_short = 20
        self.sma_long = 50
    
    def on_data(self, data):
        if len(data) < self.sma_long:
            return {'action': 'HOLD', 'confidence': 0.5}
        
        sma_20 = data['close'].rolling(self.sma_short).mean().iloc[-1]
        sma_50 = data['close'].rolling(self.sma_long).mean().iloc[-1]
        
        if sma_20 > sma_50:
            return {'action': 'BUY', 'confidence': 0.7}
        elif sma_20 < sma_50:
            return {'action': 'SELL', 'confidence': 0.7}
        
        return {'action': 'HOLD', 'confidence': 0.5}
`,
    rsi_mean_reversion: `class RSIMeanReversion(StrategyBase):
    """RSI Mean Reversion Strategy"""
    
    def setup(self):
        self.rsi_period = 14
        self.oversold = 30
        self.overbought = 70
    
    def on_data(self, data):
        if 'rsi' not in data.columns:
            return {'action': 'HOLD', 'confidence': 0.5}
        
        rsi = data['rsi'].iloc[-1]
        
        if rsi < self.oversold:
            return {'action': 'BUY', 'confidence': 0.8}
        elif rsi > self.overbought:
            return {'action': 'SELL', 'confidence': 0.8}
        
        return {'action': 'HOLD', 'confidence': 0.5}
`,
    macd_momentum: `class MACDMomentum(StrategyBase):
    """MACD Momentum Strategy"""
    
    def setup(self):
        self.fast = 12
        self.slow = 26
        self.signal = 9
    
    def on_data(self, data):
        if 'macd' not in data.columns or 'macd_signal' not in data.columns:
            return {'action': 'HOLD', 'confidence': 0.5}
        
        macd = data['macd'].iloc[-1]
        macd_signal = data['macd_signal'].iloc[-1]
        
        if macd > macd_signal:
            return {'action': 'BUY', 'confidence': 0.75}
        elif macd < macd_signal:
            return {'action': 'SELL', 'confidence': 0.75}
        
        return {'action': 'HOLD', 'confidence': 0.5}
`,
};

interface StrategyCodeEditorProps {
    strategyId: number;
}

export default function StrategyCodeEditor({ strategyId }: StrategyCodeEditorProps) {
    const [code, setCode] = useState('');
    const [hasChanges, setHasChanges] = useState(false);
    const [validation, setValidation] = useState<CodeValidation | null>(null);
    const [lastValidatedCode, setLastValidatedCode] = useState<string | null>(null);
    const validationTimeoutRef = useRef<NodeJS.Timeout>();

    const queryClient = useQueryClient();

    // Load strategy code
    const { data: strategyCode, isLoading } = useQuery<StrategyCode>({
        queryKey: ['strategy-code', strategyId],
        queryFn: () => strategyApi.getCode(strategyId),
    });

    // Validate code mutation
    const validateMutation = useMutation({
        mutationFn: (code: string) => strategyApi.validateCode(code),
        onSuccess: (data, variables) => {
            setValidation(data);
            if (data.valid) {
                setLastValidatedCode(variables);
                toast.success('Code is valid!');
            } else {
                toast.error('Code has errors');
            }
        },
        onError: () => {
            toast.error('Validation service unavailable');
        },
    });

    // Save code mutation
    const saveMutation = useMutation({
        mutationFn: (code: string) => strategyApi.updateCode(strategyId, code),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategy-code', strategyId] });
            toast.success('Code saved successfully');
            setHasChanges(false);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to save code');
        },
    });

    // Load initial code
    useEffect(() => {
        if (strategyCode?.code) {
            setCode(strategyCode.code);
            setHasChanges(false);
            setLastValidatedCode(null);
        }
    }, [strategyCode]);

    // Prevent navigation with unsaved changes
    useEffect(() => {
        const handler = (e: BeforeUnloadEvent) => {
            if (!hasChanges) return;
            e.preventDefault();
            e.returnValue = '';
        };
        window.addEventListener('beforeunload', handler);
        return () => window.removeEventListener('beforeunload', handler);
    }, [hasChanges]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl+S or Cmd+S to save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (canSave()) {
                    handleSave();
                }
            }
            // Ctrl+Enter to validate
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                if (code && !validateMutation.isPending) {
                    handleValidate();
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [code, hasChanges, validation, lastValidatedCode]);

    const handleCodeChange = (value: string | undefined) => {
        if (value !== undefined) {
            setCode(value);
            setHasChanges(true);
            setValidation(null);

            // Clear debounce timeout
            if (validationTimeoutRef.current) {
                clearTimeout(validationTimeoutRef.current);
            }
        }
    };

    const handleTemplateSelect = (template: keyof typeof CODE_TEMPLATES) => {
        // Confirm overwrite if there are unsaved changes
        if (hasChanges) {
            if (!confirm('You have unsaved changes. Load template and discard changes?')) {
                return;
            }
        }

        setCode(CODE_TEMPLATES[template]);
        setHasChanges(true);
        setValidation(null);
        setLastValidatedCode(null);
    };

    const handleValidate = () => {
        if (!code.trim()) {
            toast.error('Code cannot be empty');
            return;
        }
        validateMutation.mutate(code);
    };

    const canSave = () => {
        return hasChanges &&
            !saveMutation.isPending &&
            validation?.valid &&
            code === lastValidatedCode;
    };

    const handleSave = () => {
        if (!canSave()) {
            if (!validation?.valid) {
                toast.error('Please validate code before saving');
            } else if (code !== lastValidatedCode) {
                toast.error('Code has changed since validation. Please re-validate.');
            }
            return;
        }
        saveMutation.mutate(code);
    };

    if (isLoading) {
        return (
            <div className="w-full h-96 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
                <p className="text-gray-500">Loading code editor...</p>
            </div>
        );
    }

    return (
        <div className="w-full space-y-4">
            {/* Strategy Metadata */}
            {strategyCode && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                        <div className="flex-1">
                            <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                                {strategyCode.name}
                            </h3>
                            <div className="flex gap-4 mt-1 text-sm text-blue-700 dark:text-blue-300">
                                <span>Platform: {strategyCode.platform}</span>
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    Last updated: {new Date().toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Security Warning Banner */}
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div>
                        <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                            ⚠ Strategy code runs in a restricted sandbox.
                        </p>
                        <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                            Dangerous imports, file access, and system calls are blocked.
                        </p>
                    </div>
                </div>
            </div>

            {/* Header with Template Selector */}
            <div className="flex flex-wrap gap-3 items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <Code2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Templates:
                        </span>
                    </div>
                    <select
                        onChange={(e) => e.target.value && handleTemplateSelect(e.target.value as keyof typeof CODE_TEMPLATES)}
                        className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-900 dark:text-white"
                        value=""
                    >
                        <option value="">Select a template...</option>
                        <option value="sma_crossover">SMA Crossover</option>
                        <option value="rsi_mean_reversion">RSI Mean Reversion</option>
                        <option value="macd_momentum">MACD Momentum</option>
                    </select>
                </div>

                {/* Keyboard Shortcuts Hint */}
                <div className="text-xs text-gray-500 dark:text-gray-400">
                    <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">Ctrl+Enter</kbd> to validate
                    {' • '}
                    <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">Ctrl+S</kbd> to save
                </div>
            </div>

            {/* Code Editor */}
            <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
                <Editor
                    height="500px"
                    defaultLanguage="python"
                    value={code}
                    onChange={handleCodeChange}
                    theme="vs-dark"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: 'on',
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                    }}
                />
            </div>

            {/* Validation Results */}
            {validation && (
                <div className={`p-4 rounded-lg ${validation.valid
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                    }`}>
                    <div className="flex items-start gap-2">
                        {validation.valid ? (
                            <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                        ) : (
                            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                        )}
                        <div className="flex-1">
                            <h4 className={`font-semibold ${validation.valid ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'
                                }`}>
                                {validation.valid ? 'Code is valid' : 'Validation failed'}
                            </h4>
                            {validation.errors.length > 0 && (
                                <ul className="mt-2 space-y-1">
                                    {validation.errors.map((error, i) => (
                                        <li key={i} className="text-sm text-red-700 dark:text-red-300">
                                            • {error}
                                        </li>
                                    ))}
                                </ul>
                            )}
                            {validation.warnings.length > 0 && (
                                <ul className="mt-2 space-y-1">
                                    {validation.warnings.map((warning, i) => (
                                        <li key={i} className="text-sm text-yellow-700 dark:text-yellow-300">
                                            ⚠ {warning}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Validation Required Warning */}
            {hasChanges && code !== lastValidatedCode && (
                <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
                    <p className="text-sm text-orange-800 dark:text-orange-200">
                        Code has changed since last validation. Please validate before saving.
                    </p>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
                <button
                    onClick={handleValidate}
                    disabled={!code.trim() || validateMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    title="Validate code (Ctrl+Enter)"
                >
                    <Play className="w-4 h-4" />
                    {validateMutation.isPending ? 'Validating...' : 'Test Code'}
                </button>
                <button
                    onClick={handleSave}
                    disabled={!canSave()}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    title={!canSave() ? 'Validate code first' : 'Save code (Ctrl+S)'}
                >
                    <Save className="w-4 h-4" />
                    {saveMutation.isPending ? 'Saving...' : 'Save Code'}
                </button>
            </div>
        </div>
    );
}
