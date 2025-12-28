// QUAD v1.1 API Service

import api from './client';
import type {
  TradeIntentResponse,
  ConvictionTimeline,
  PillarDriftMeasurement,
  DecisionHistory,
  DecisionHistoryEntry,
  DecisionStatistics,
} from './types';

/**
 * QUAD Reasoning API Service
 * Provides access to QUAD v1.1 analysis and observability features
 */
export const QuadService = {
  /**
   * Get QUAD reasoning analysis for a symbol (v1.1)
   * Returns TradeIntent with calibration versioning
   */
  getAnalysis: async (symbol: string): Promise<TradeIntentResponse> => {
    const response = await api.get(`/reasoning/${symbol}/reasoning`);
    return response.data;
  },

  /**
   * Get conviction timeline for a symbol
   * Shows how conviction has evolved over time
   * 
   * @param symbol - Stock symbol (e.g., "RELIANCE")
   * @param days - Number of days to look back (default: 30)
   */
  getConvictionTimeline: async (
    symbol: string,
    days: number = 30
  ): Promise<ConvictionTimeline> => {
    const response = await api.get(`/decisions/conviction-timeline/${symbol}`, {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get pillar drift measurement
   * Shows which pillars changed and by how much
   * 
   * @param symbol - Stock symbol
   * @param compareLatest - If true, compare latest two decisions (default: true)
   * @param fromTimestamp - ISO timestamp of earlier decision (for custom comparison)
   * @param toTimestamp - ISO timestamp of later decision (for custom comparison)
   */
  getPillarDrift: async (
    symbol: string,
    compareLatest: boolean = true,
    fromTimestamp?: string,
    toTimestamp?: string
  ): Promise<PillarDriftMeasurement> => {
    const params: any = { compare_latest: compareLatest };
    if (fromTimestamp) params.from_timestamp = fromTimestamp;
    if (toTimestamp) params.to_timestamp = toTimestamp;

    const response = await api.get(`/decisions/pillar-drift/${symbol}`, { params });
    return response.data;
  },

  /**
   * Get decision history for a symbol
   * Returns historical TradeIntent decisions
   * 
   * @param symbol - Stock symbol
   * @param limit - Maximum number of decisions to return
   * @param days - Number of days to look back
   */
  getDecisionHistory: async (
    symbol: string,
    limit?: number,
    days?: number
  ): Promise<DecisionHistory> => {
    const params: any = {};
    if (limit) params.limit = limit;
    if (days) params.days = days;

    const response = await api.get(`/decisions/history/${symbol}`, { params });
    return response.data;
  },

  /**
   * Get latest decision for a symbol
   * Returns the most recent TradeIntent decision
   * 
   * @param symbol - Stock symbol
   */
  getLatestDecision: async (symbol: string): Promise<DecisionHistoryEntry> => {
    const response = await api.get(`/decisions/latest/${symbol}`);
    return response.data;
  },

  /**
   * Get decision statistics for a symbol
   * Returns aggregate metrics about decision history
   * 
   * @param symbol - Stock symbol
   * @param days - Number of days to analyze (default: 30)
   */
  getStatistics: async (
    symbol: string,
    days: number = 30
  ): Promise<DecisionStatistics> => {
    const response = await api.get(`/decisions/statistics/${symbol}`, {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get backtest results and equity curve for a symbol
   * 
   * @param symbol - Stock symbol
   * @param initialCapital - Initial simulation capital (default: 100000)
   */
  getBacktest: async (
    symbol: string,
    initialCapital: number = 100000
  ): Promise<any> => {
    const response = await api.get(`/quad/${symbol}/backtest`, {
      params: { initial_capital: initialCapital },
    });
    return response.data;
  },
};

/**
 * Helper function to check if v1.1 features are available
 */
export const isQuadV11Available = (analysis: TradeIntentResponse): boolean => {
  return analysis.contract_version >= "1.1.0";
};

/**
 * Helper function to format calibration version for display
 */
export const formatCalibrationVersion = (version?: string): string => {
  if (!version) return "Unknown";
  
  // Convert "matrix_2024_q4" to "Matrix 2024 Q4"
  return version
    .split("_")
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

/**
 * Helper function to get bias color class
 */
export const getBiasColorClass = (bias: string): string => {
  switch (bias.toUpperCase()) {
    case "BULLISH":
      return "text-emerald-500";
    case "BEARISH":
      return "text-rose-500";
    case "NEUTRAL":
      return "text-muted-foreground";
    case "INVALID":
      return "text-amber-500";
    default:
      return "text-muted-foreground";
  }
};

/**
 * Helper function to get drift classification color
 */
export const getDriftColorClass = (classification: string): string => {
  switch (classification.toUpperCase()) {
    case "STABLE":
      return "text-emerald-500";
    case "MODERATE":
      return "text-amber-500";
    case "HIGH":
      return "text-rose-500";
    default:
      return "text-muted-foreground";
  }
};

export default QuadService;
