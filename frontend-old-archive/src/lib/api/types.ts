// QUAD v1.1 TypeScript Interfaces

/**
 * QUAD v1.0 Base Types (FROZEN - No Changes)
 */

export enum DirectionalBias {
  BULLISH = "BULLISH",
  BEARISH = "BEARISH",
  NEUTRAL = "NEUTRAL",
  INVALID = "INVALID",
}

export interface PillarScore {
  score: number;
  bias: string;
  is_placeholder: boolean;
  weight: number;
  metrics?: Record<string, any>;
}

export interface AnalysisQuality {
  total_pillars: number;
  active_pillars: number;
  placeholder_pillars: number;
  failed_pillars: string[];
  // v1.1 additions (optional for backward compatibility)
  calibration_version?: string;
  pillar_weights_snapshot?: Record<string, number>;
}

export interface TradeIntentResponse {
  symbol: string;
  analysis_timestamp: string;
  contract_version: string;
  decision_id?: string; // v1.1 addition
  
  // Core reasoning
  directional_bias: string;
  conviction_score: number;
  
  // Explainability
  reasoning: string;
  pillar_scores: Record<string, PillarScore>;
  
  // Quality metadata
  quality: AnalysisQuality;
  
  // Validity flags
  is_valid: boolean;
  is_execution_ready: boolean;
  execution_block_reason?: string;
  warnings?: string[];
  
  // Market context
  market_context?: {
    regime: string;
    vix_level?: number;
  };
  
  // Technical state
  technical_state?: {
    ltp: number;
    sma_50?: number;
    sma_200?: number;
    rsi?: number;
    macd?: number;
    [key: string]: any;
  };
}

/**
 * QUAD v1.1 New Types
 */

export interface ConvictionDataPoint {
  timestamp: string;
  conviction_score: number;
  directional_bias: string;
  active_pillars: number;
  calibration_version?: string;
  data_age_seconds?: number;
}

export interface ConvictionTimeline {
  symbol: string;
  data_points: ConvictionDataPoint[];
  start_time?: string;
  end_time?: string;
  sample_count: number;
  
  // Computed metrics
  conviction_volatility: number;
  bias_consistency: number;
  average_conviction: number;
  conviction_trend: string; // INCREASING/DECREASING/STABLE
  recent_bias: string;
  bias_streak_count: number;
  conviction_percentiles: {
    p25: number;
    p50: number;
    p75: number;
  };
}

export interface PillarScoreSnapshot {
  timestamp: string;
  scores: Record<string, number>;
  biases: Record<string, string>;
  placeholder_pillars: string[];
  failed_pillars: string[];
  calibration_version?: string;
}

export interface BiasChange {
  from: string;
  to: string;
}

export interface TopMover {
  pillar: string;
  delta: number;
  previous_bias: string;
  current_bias: string;
}

export interface PillarDriftMeasurement {
  symbol: string;
  previous_snapshot: PillarScoreSnapshot;
  current_snapshot: PillarScoreSnapshot;
  score_deltas: Record<string, number>;
  bias_changes: Record<string, BiasChange>;
  max_drift_pillar: string;
  max_drift_magnitude: number;
  total_drift_score: number;
  time_delta_seconds: number;
  calibration_changed: boolean;
  
  // Computed helpers
  drift_classification: string; // STABLE/MODERATE/HIGH
  top_movers: TopMover[];
  drift_summary: string;
}

export interface DecisionHistoryEntry {
  decision_id: string;
  symbol: string;
  analysis_timestamp: string;
  directional_bias: string;
  conviction_score: number;
  calibration_version?: string;
  pillar_count_active: number;
  pillar_count_placeholder: number;
  pillar_count_failed: number;
  engine_version: string;
  contract_version: string;
  created_at?: string;
  is_superseded: boolean;
  pillar_scores?: Record<string, number>;
  pillar_biases?: Record<string, string>;
}

export interface DecisionHistory {
  symbol: string;
  entries: DecisionHistoryEntry[];
  earliest_decision?: string;
  latest_decision?: string;
  total_decisions: number;
}

export interface DecisionStatistics {
  symbol: string;
  total_decisions: number;
  days_analyzed: number;
  average_conviction: number;
  bias_distribution: Record<string, number>;
  conviction_range: [number, number];
  earliest_decision?: string;
  latest_decision?: string;
}

/**
 * API Error Response
 */
export interface ApiError {
  detail: string;
  status?: number;
}
