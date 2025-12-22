/**
 * Mock API Response Data for E2E Tests
 * Matches TradeIntent v1.0 contract from backend validation tests
 */

export const mockTradeIntentResponse = {
  symbol: 'RELIANCE',
  analysis_timestamp: '2025-12-23T00:00:00Z',
  contract_version: '1.0.0',
  directional_bias: 'BULLISH',
  conviction_score: 70.2,
  reasoning:
    'Bias: BULLISH (Conviction: 70%) | Momentum: 100 (BULLISH) | Regime: 85 (BULLISH) | Trend: 50 (NEUTRAL)',
  pillar_scores: {
    trend: {
      score: 50.0,
      bias: 'NEUTRAL',
      is_placeholder: false,
      weight: 0.3,
    },
    momentum: {
      score: 100.0,
      bias: 'BULLISH',
      is_placeholder: false,
      weight: 0.2,
    },
    volatility: {
      score: 60.0,
      bias: 'NEUTRAL',
      is_placeholder: true,
      weight: 0.1,
    },
    liquidity: {
      score: 81.5,
      bias: 'NEUTRAL',
      is_placeholder: true,
      weight: 0.1,
    },
    sentiment: {
      score: 50.0,
      bias: 'NEUTRAL',
      is_placeholder: false,
      weight: 0.1,
    },
    regime: {
      score: 85.0,
      bias: 'BULLISH',
      is_placeholder: false,
      weight: 0.2,
    },
  },
  quality: {
    total_pillars: 6,
    active_pillars: 4,
    placeholder_pillars: 2,
    failed_pillars: [],
    data_age_seconds: 5,
  },
  is_valid: true,
  is_execution_ready: true,
  warnings: [
    'Volatility pillar is placeholder (returns neutral)',
    'Liquidity pillar is placeholder (returns neutral)',
  ],
  market_context: {
    regime: 'BULLISH',
    vix_level: 15.5,
  },
  technical_state: {
    ltp: 2500.0,
    sma_50: 2450.0,
    sma_200: 2400.0,
    rsi: 65.0,
  },
};

export const mockTradeIntentNotReady = {
  ...mockTradeIntentResponse,
  directional_bias: 'NEUTRAL',
  conviction_score: 45.0,
  is_execution_ready: false,
  quality: {
    total_pillars: 6,
    active_pillars: 3,
    placeholder_pillars: 3,
    failed_pillars: [],
  },
  warnings: [
    'Volatility pillar is placeholder (returns neutral)',
    'Liquidity pillar is placeholder (returns neutral)',
    'Analysis not execution-ready (placeholders or failures present)',
  ],
};

export const mockTradeIntentWithFailures = {
  ...mockTradeIntentResponse,
  directional_bias: 'INVALID',
  conviction_score: 0,
  is_valid: false,
  is_execution_ready: false,
  quality: {
    total_pillars: 6,
    active_pillars: 4,
    placeholder_pillars: 0,
    failed_pillars: ['trend', 'momentum'],
  },
  warnings: ['Trend pillar failed during analysis', 'Momentum pillar failed during analysis'],
};
