'use client';

import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Loader2, CheckCircle2, AlertCircle, Play, Save } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';

interface StrategyEditorProps {
    strategyId?: number;
    initialCode?: string;
    onSave?: (code: string) => Promise<void>;
    onValidate?: (code: string) => Promise<ValidationResult>;
}

interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
    timestamp: string;
}

const DEFAULT_STRATEGY_TEMPLATE = `from strategy_dsl import StrategyBase

class MyStrategy(StrategyBase):
    \"\"\"
    Custom trading strategy using QUAD DSL.
    
    Available methods:
    - self.sma(data, period) - Simple Moving Average
    - self.rsi(data, period) - Relative Strength Index
    - self.macd(data) - MACD indicator
    - self.buy(quantity, stop_loss, take_profit) - Generate BUY signal
    - self.sell(quantity, stop_loss, take_profit) - Generate SELL signal
    - self.hold() - Generate HOLD signal
    \"\"\"
    
    def setup(self):
        \"\"\"Initialize strategy parameters\"\"\"
        self.fast_period = 20
        self.slow_period = 50
        self.quantity = 100
    
    def on_data(self, data):
        \"\"\"
        Called with new market data.
        
        Args:
            data: DataFrame with columns [open, high, low, close, volume]
        
        Returns:
            Signal dict with action, quantity, stop_loss, take_profit
        \"\"\"
        # Calculate indicators
        fast_sma = self.sma(data, self.fast_period)
        slow_sma = self.sma(data, self.slow_period)
        
        # Get current values
        current_fast = fast_sma.iloc[-1]
        current_slow = slow_sma.iloc[-1]
        prev_fast = fast_sma.iloc[-2] if len(fast_sma) > 1 else current_fast
        prev_slow = slow_sma.iloc[-2] if len(slow_sma) > 1 else current_slow
        
        # Bullish crossover
        if prev_fast <= prev_slow and current_fast > current_slow:
            return self.buy(
                quantity=self.quantity,
                stop_loss=0.02,  # 2% stop loss
                take_profit=0.05  # 5% take profit
            )
        
        # Bearish crossover
        elif prev_fast >= prev_slow and current_fast < current_slow:
            return self.sell(
                quantity=self.quantity,
                stop_loss=0.02,
                take_profit=0.05
            )
        
        # No signal
        return self.hold()
`;

export default function StrategyEditor({
    strategyId,
    initialCode,
    onSave,
    onValidate
}: StrategyEditorProps) {
    const [code, setCode] = useState(initialCode || DEFAULT_STRATEGY_TEMPLATE);
    const [validation, setValidation] = useState<ValidationResult | null>(null);
    const [isValidating, setIsValidating] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [lastSaved, setLastSaved] = useState<Date | null>(null);

    // Auto-validate on code change (debounced)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (onValidate && code) {
                handleValidate();
            }
        }, 1000);

        return () => clearTimeout(timer);
    }, [code]);

    const handleValidate = async () => {
        if (!onValidate) return;

        setIsValidating(true);
        try {
            const result = await onValidate(code);
            setValidation(result);
        } catch (error) {
            console.error('Validation error:', error);
        } finally {
            setIsValidating(false);
        }
    };

    const handleSave = async () => {
        if (!onSave) return;

        setIsSaving(true);
        try {
            await onSave(code);
            setLastSaved(new Date());
        } catch (error) {
            console.error('Save error:', error);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* Editor Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold">Strategy Code Editor</h3>
                    {isValidating && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Validating...
                        </div>
                    )}
                    {validation && !isValidating && (
                        <div className={`flex items-center gap-2 text-sm ${validation.valid ? 'text-green-600' : 'text-red-600'
                            }`}>
                            {validation.valid ? (
                                <>
                                    <CheckCircle2 className="w-4 h-4" />
                                    Valid
                                </>
                            ) : (
                                <>
                                    <AlertCircle className="w-4 h-4" />
                                    {validation.errors.length} error(s)
                                </>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {lastSaved && (
                        <span className="text-xs text-muted-foreground">
                            Saved {lastSaved.toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        onClick={handleSave}
                        disabled={isSaving || (validation && !validation.valid)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSaving ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                Save Code
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Monaco Editor */}
            <Card>
                <CardContent className="p-0">
                    <Editor
                        height="600px"
                        defaultLanguage="python"
                        value={code}
                        onChange={(value) => setCode(value || '')}
                        theme="vs-dark"
                        options={{
                            minimap: { enabled: true },
                            fontSize: 14,
                            lineNumbers: 'on',
                            roundedSelection: false,
                            scrollBeyondLastLine: false,
                            readOnly: false,
                            automaticLayout: true,
                            tabSize: 4,
                            insertSpaces: true,
                        }}
                    />
                </CardContent>
            </Card>

            {/* Validation Results */}
            {validation && (
                <div className="space-y-2">
                    {/* Errors */}
                    {validation.errors.length > 0 && (
                        <Card className="border-red-500">
                            <CardHeader>
                                <CardTitle className="text-red-600 flex items-center gap-2">
                                    <AlertCircle className="w-5 h-5" />
                                    Errors ({validation.errors.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="list-disc list-inside space-y-1">
                                    {validation.errors.map((error, idx) => (
                                        <li key={idx} className="text-sm text-red-600">{error}</li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}

                    {/* Warnings */}
                    {validation.warnings.length > 0 && (
                        <Card className="border-yellow-500">
                            <CardHeader>
                                <CardTitle className="text-yellow-600 flex items-center gap-2">
                                    <AlertCircle className="w-5 h-5" />
                                    Warnings ({validation.warnings.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="list-disc list-inside space-y-1">
                                    {validation.warnings.map((warning, idx) => (
                                        <li key={idx} className="text-sm text-yellow-600">{warning}</li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}

            {/* Help Text */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Quick Reference</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-2">
                    <div>
                        <strong>Available Indicators:</strong>
                        <ul className="list-disc list-inside ml-4 text-muted-foreground">
                            <li><code>self.sma(data, period)</code> - Simple Moving Average</li>
                            <li><code>self.rsi(data, period)</code> - Relative Strength Index</li>
                            <li><code>self.macd(data)</code> - MACD</li>
                        </ul>
                    </div>
                    <div>
                        <strong>Signal Methods:</strong>
                        <ul className="list-disc list-inside ml-4 text-muted-foreground">
                            <li><code>self.buy(quantity, stop_loss, take_profit)</code></li>
                            <li><code>self.sell(quantity, stop_loss, take_profit)</code></li>
                            <li><code>self.hold()</code></li>
                        </ul>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
