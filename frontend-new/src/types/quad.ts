// TypeScript interfaces for TradeIntent v1.0 contract
// Maps to backend: backend/app/core/trade_intent.py

export type DirectionalBias = 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'INVALID';

export interface PillarContribution {
  name: string;                 // "trend", "momentum", "volatility", etc.
  score: number;                // 0-100
  bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  is_placeholder: boolean;      // True if returning hardcoded neutral
  weight_applied: number;       // Weight used in aggregation (e.g., 0.30)
}

export interface AnalysisQuality {
  total_pillars: number;        // Should always be 6
  active_pillars: number;       // Pillars with real logic implemented
  placeholder_pillars: number;  // Pillars returning neutral defaults
  failed_pillars: string[];     // Pillars that threw exceptions
  data_age_seconds?: number;    // Age of input snapshot
}

export interface TradeIntent {
  // Identity
  symbol: string;
  analysis_timestamp: string;   // ISO datetime
  
  // Core Reasoning Output
  directional_bias: DirectionalBias;
  conviction_score: number;      // 0-100 (how confident the logic is)
  
  // Explainability
  pillar_contributions: PillarContribution[];
  reasoning_narrative: string;   // Human-readable explanation
  
  // Quality Metadata (NEW in v1.0)
  quality: AnalysisQuality;
  
  // Validity Flags (NEW in v1.0)
  is_analysis_valid: boolean;     // False if critical data missing
  is_execution_ready: boolean;    // False if placeholder pillars > threshold
  degradation_warnings: string[]; // E.g., "Volatility pillar is placeholder"
  
  // Version & Schema
  contract_version: string;       // "1.0.0"
}

// API Response structure (from ReasoningService)
export interface ReasoningAPIResponse {
  symbol: string;
  analysis_timestamp: string;
  contract_version: string;
  
  // Core reasoning
  directional_bias: DirectionalBias;
  conviction_score: number;
  
  // Explainability
  reasoning: string;
  pillar_scores: {
    [key: string]: {
      score: number;
      bias: string;
      is_placeholder: boolean;
      weight: number;
    };
  };
  
  // Quality metadata
  quality: AnalysisQuality;
  
  // Validity flags
  is_valid: boolean;
  is_execution_ready: boolean;
  warnings: string[];
  
  // Market context (optional)
  market_context?: {
    regime: string;
    vix_level: number;
  };
  
  // Technical state (optional)
  technical_state?: {
    ltp: number;
    sma_50: number;
    sma_200: number;
    rsi: number;
  };
}
