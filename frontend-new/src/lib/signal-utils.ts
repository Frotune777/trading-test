/**
 * Signal Aggregation Utilities
 * 
 * Functions to calculate aggregated technical signals from 50+ indicators
 */

export interface TechnicalSignal {
  score: number // 0-100
  bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  strength: 'STRONG' | 'MODERATE' | 'WEAK'
  signals: {
    trend: {
      direction: 'UP' | 'DOWN' | 'SIDEWAYS'
      bullish: number
      total: number
    }
    momentum: {
      state: 'STRONG' | 'WEAK' | 'OVERSOLD' | 'OVERBOUGHT' | 'NEUTRAL'
      bullish: number
      total: number
    }
    volume: {
      state: 'ACCUMULATION' | 'DISTRIBUTION' | 'NEUTRAL'
      bullish: number
      total: number
    }
    volatility: {
      level: 'HIGH' | 'NORMAL' | 'LOW'
    }
  }
}

export interface TechnicalIndicator {
  [key: string]: number | string
}

/**
 * Helper function to get indicator value case-insensitively
 */
function getIndicator(indicators: TechnicalIndicator, key: string): number | undefined {
  // Try exact match first
  if (indicators[key] !== undefined) {
    const val = indicators[key]
    return typeof val === 'number' ? val : parseFloat(String(val))
  }
  
  // Try case-insensitive match
  const lowerKey = key.toLowerCase()
  for (const [k, v] of Object.entries(indicators)) {
    if (k.toLowerCase() === lowerKey) {
      return typeof v === 'number' ? v : parseFloat(String(v))
    }
  }
  
  return undefined
}

/**
 * Calculate aggregated technical signal from all indicators
 */
export function calculateTechnicalSignal(indicators: TechnicalIndicator): TechnicalSignal {
  const trendSignals = getTrendSignals(indicators)
  const momentumSignals = getMomentumSignals(indicators)
  const volumeSignals = getVolumeSignals(indicators)
  const volatilitySignals = getVolatilitySignals(indicators)

  // Calculate weighted score (0-100)
  let score = 50 // Start neutral

  // Trend indicators (40% weight = ±20 points)
  const trendWeight = 20 * (trendSignals.bullish / trendSignals.total)
  score += trendWeight - 10

  // Momentum indicators (30% weight = ±15 points)
  const momentumWeight = 15 * (momentumSignals.bullish / momentumSignals.total)
  score += momentumWeight - 7.5

  // Volume indicators (20% weight = ±10 points)
  const volumeWeight = 10 * (volumeSignals.bullish / volumeSignals.total)
  score += volumeWeight - 5

  // Volatility adjustment (10% weight = ±5 points)
  if (volatilitySignals.level === 'LOW') score += 5
  else if (volatilitySignals.level === 'HIGH') score -= 2.5

  // Clamp to 0-100
  score = Math.max(0, Math.min(100, score))

  // Determine bias and strength
  const bias = score > 60 ? 'BULLISH' : score < 40 ? 'BEARISH' : 'NEUTRAL'
  const strength = Math.abs(score - 50) > 20 ? 'STRONG' : 
                   Math.abs(score - 50) > 10 ? 'MODERATE' : 'WEAK'

  return {
    score,
    bias,
    strength,
    signals: {
      trend: trendSignals,
      momentum: momentumSignals,
      volume: volumeSignals,
      volatility: volatilitySignals
    }
  }
}

/**
 * Analyze trend indicators
 */
function getTrendSignals(indicators: TechnicalIndicator) {
  let bullish = 0
  let total = 0

  // SMA crossovers
  const sma50 = getIndicator(indicators, 'SMA_50')
  const sma200 = getIndicator(indicators, 'SMA_200')
  if (sma50 !== undefined && sma200 !== undefined) {
    total++
    if (sma50 > sma200) bullish++
  }

  // Price vs EMAs
  const close = getIndicator(indicators, 'Close')
  const ema20 = getIndicator(indicators, 'EMA_20')
  if (close !== undefined && ema20 !== undefined) {
    total++
    if (close > ema20) bullish++
  }

  if (close !== undefined && sma50 !== undefined) {
    total++
    if (close > sma50) bullish++
  }

  // ADX strength
  const adx = getIndicator(indicators, 'ADX')
  if (adx !== undefined) {
    total++
    if (adx > 25) {
      // Strong trend - check if uptrend
      if (close && sma50 && close > sma50) {
        bullish++
      }
    }
  }

  // EMA alignment (20 > 50)
  const ema50 = getIndicator(indicators, 'EMA_50')
  if (ema20 !== undefined && ema50 !== undefined) {
    total++
    if (ema20 > ema50) bullish++
  }

  // Parabolic SAR
  const sar = getIndicator(indicators, 'SAR')
  if (sar !== undefined && close !== undefined) {
    total++
    if (close > sar) bullish++
  }

  const direction: 'UP' | 'DOWN' | 'SIDEWAYS' = total > 0 ? (bullish / total > 0.6 ? 'UP' : bullish / total < 0.4 ? 'DOWN' : 'SIDEWAYS') : 'SIDEWAYS'

  return { direction, bullish, total: Math.max(total, 1) } // Ensure total is at least 1 to avoid division by zero
}

/**
 * Analyze momentum indicators
 */
function getMomentumSignals(indicators: TechnicalIndicator) {
  let bullish = 0
  let total = 0
  let state: 'STRONG' | 'WEAK' | 'OVERSOLD' | 'OVERBOUGHT' | 'NEUTRAL' = 'NEUTRAL'

  // RSI
  const rsi = getIndicator(indicators, 'RSI')
  if (rsi !== undefined) {
    total++
    if (rsi > 50) bullish++
    if (rsi < 30) state = 'OVERSOLD'
    else if (rsi > 70) state = 'OVERBOUGHT'
  }

  // MACD
  const macd = getIndicator(indicators, 'MACD')
  const macdSignal = getIndicator(indicators, 'MACD_Signal')
  if (macd !== undefined && macdSignal !== undefined) {
    total++
    if (macd > macdSignal) bullish++
  }

  // Stochastic
  const stochK = getIndicator(indicators, 'Stochastic_K')
  if (stochK !== undefined) {
    total++
    if (stochK > 50) bullish++
  }

  // CCI
  const cci = getIndicator(indicators, 'CCI')
  if (cci !== undefined) {
    total++
    if (cci > 0) bullish++
  }

  // ROC (Rate of Change)
  const roc = getIndicator(indicators, 'ROC')
  if (roc !== undefined) {
    total++
    if (roc > 0) bullish++
  }

  // Determine overall momentum state
  if (state === 'NEUTRAL' && total > 0) {
    state = bullish / total > 0.7 ? 'STRONG' : bullish / total < 0.3 ? 'WEAK' : 'NEUTRAL'
  }

  return { state, bullish, total: Math.max(total, 1) }
}

/**
 * Analyze volume indicators
 */
function getVolumeSignals(indicators: TechnicalIndicator) {
  let bullish = 0
  let total = 0

  // OBV trend
  const obv = getIndicator(indicators, 'OBV')
  const obvSma = getIndicator(indicators, 'OBV_SMA')
  if (obv !== undefined && obvSma !== undefined) {
    total++
    if (obv > obvSma) bullish++
  }

  // Volume vs SMA
  const volume = getIndicator(indicators, 'Volume')
  const volumeSma = getIndicator(indicators, 'Volume_SMA')
  if (volume !== undefined && volumeSma !== undefined) {
    total++
    if (volume > volumeSma) bullish++
  }

  // MFI (Money Flow Index)
  const mfi = getIndicator(indicators, 'MFI')
  if (mfi !== undefined) {
    total++
    if (mfi > 50) bullish++
  }

  const state: 'ACCUMULATION' | 'DISTRIBUTION' | 'NEUTRAL' = total > 0 ? (bullish / total > 0.6 ? 'ACCUMULATION' : 
                bullish / total < 0.4 ? 'DISTRIBUTION' : 'NEUTRAL') : 'NEUTRAL'

  return { state, bullish, total: Math.max(total, 1) }
}

/**
 * Analyze volatility indicators
 */
function getVolatilitySignals(indicators: TechnicalIndicator) {
  let level: 'HIGH' | 'NORMAL' | 'LOW' = 'NORMAL'

  // ATR analysis
  const atr = getIndicator(indicators, 'ATR')
  const atrSma = getIndicator(indicators, 'ATR_SMA')
  if (atr !== undefined && atrSma !== undefined) {
    if (atr > atrSma * 1.5) level = 'HIGH'
    else if (atr < atrSma * 0.7) level = 'LOW'
  }

  // Bollinger Band width
  const bbUpper = getIndicator(indicators, 'BB_Upper')
  const bbLower = getIndicator(indicators, 'BB_Lower')
  const close = getIndicator(indicators, 'Close')
  if (bbUpper !== undefined && bbLower !== undefined && close !== undefined && close > 0) {
    const bbWidth = (bbUpper - bbLower) / close
    
    if (bbWidth > 0.15) level = 'HIGH'
    else if (bbWidth < 0.05) level = 'LOW'
  }

  return { level }
}

/**
 * Get human-readable signal description
 */
export function getSignalDescription(signal: TechnicalSignal): string {
  const { bias, strength, score } = signal

  if (bias === 'BULLISH') {
    if (strength === 'STRONG') return `Strong bullish signal (${score.toFixed(0)}/100). Multiple indicators confirm upward momentum.`
    if (strength === 'MODERATE') return `Moderate bullish signal (${score.toFixed(0)}/100). Trend is positive but not overwhelming.`
    return `Weak bullish signal (${score.toFixed(0)}/100). Slight upward bias with mixed indicators.`
  }

  if (bias === 'BEARISH') {
    if (strength === 'STRONG') return `Strong bearish signal (${score.toFixed(0)}/100). Multiple indicators confirm downward pressure.`
    if (strength === 'MODERATE') return `Moderate bearish signal (${score.toFixed(0)}/100). Trend is negative but not extreme.`
    return `Weak bearish signal (${score.toFixed(0)}/100). Slight downward bias with mixed indicators.`
  }

  return `Neutral signal (${score.toFixed(0)}/100). Indicators are mixed with no clear direction.`
}
