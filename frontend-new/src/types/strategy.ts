/**
 * Strategy Management Types
 */

export type Platform = 'TradingView' | 'ChartInk' | 'Python' | 'Manual';
export type TradingMode = 'LONG' | 'SHORT' | 'BOTH';

export interface Strategy {
  id: number;
  name: string;
  webhook_id: string;
  webhook_url: string;
  user_id: string;
  platform: Platform;
  is_active: boolean;
  is_intraday: boolean;
  trading_mode: TradingMode;
  start_time?: string;
  end_time?: string;
  squareoff_time?: string;
  description?: string;
  symbol_count: number;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreate {
  name: string;
  platform: Platform;
  is_intraday?: boolean;
  trading_mode?: TradingMode;
  start_time?: string;
  end_time?: string;
  squareoff_time?: string;
  description?: string;
}

export interface StrategyUpdate {
  name?: string;
  is_active?: boolean;
  is_intraday?: boolean;
  trading_mode?: TradingMode;
  start_time?: string;
  end_time?: string;
  squareoff_time?: string;
  description?: string;
}

export interface SymbolMapping {
  id: number;
  strategy_id: number;
  symbol: string;
  exchange: string;
  quantity: number;
  product_type: string;
  broker?: string;
  created_at: string;
}

export interface SymbolMappingCreate {
  symbol: string;
  exchange: string;
  quantity: number;
  product_type: string;
  broker?: string;
}
